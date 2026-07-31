from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from log_aggregator.models import Project, AnomalyAlert
from log_aggregator.clickhouse_client import get_client

class Command(BaseCommand):
    help = 'Detects anomalies in log ingestion (spikes in ERRORs)'

    def handle(self, *args, **options):
        now = timezone.now()
        five_mins_ago = now - timedelta(minutes=5)
        one_hour_ago = now - timedelta(hours=1)

        projects = Project.objects.all()
        
        ch_client = get_client()
        if not ch_client:
            self.stderr.write("FATAL: Could not connect to ClickHouse")
            return
            
        five_mins_ago_str = five_mins_ago.strftime('%Y-%m-%d %H:%M:%S')
        one_hour_ago_str = one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')

        for project in projects:
            project_id = str(project.id)
            
            # Historical errors in last 1 hour
            hist_query = f"SELECT count() FROM log_entries WHERE project_id = '{project_id}' AND level = 'ERROR' AND timestamp >= '{one_hour_ago_str}' AND timestamp < '{five_mins_ago_str}'"
            hist_result = ch_client.query(hist_query)
            historical_errors = hist_result.result_rows[0][0]

            # Current errors in last 5 mins
            curr_query = f"SELECT count() FROM log_entries WHERE project_id = '{project_id}' AND level = 'ERROR' AND timestamp >= '{five_mins_ago_str}'"
            curr_result = ch_client.query(curr_query)
            current_errors = curr_result.result_rows[0][0]

            # Baseline calculation (avg per 5 min in the hour)
            # The hour prior to the last 5 mins is 55 mins = 11 intervals of 5 mins
            baseline_avg_per_5_min = historical_errors / 11.0 if historical_errors > 0 else 0

            # Simple anomaly threshold: if current > baseline * 3 and current > 5
            if current_errors > 5 and current_errors > (baseline_avg_per_5_min * 3):
                alert_msg = f"Spike in ERRORs detected! {current_errors} in last 5 mins (Baseline: {baseline_avg_per_5_min:.1f})"
                AnomalyAlert.objects.create(
                    project=project,
                    description=alert_msg
                )
                self.stdout.write(self.style.WARNING(f"[{project.name}] {alert_msg}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"[{project.name}] Normal. {current_errors} errors."))
