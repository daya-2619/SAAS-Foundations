from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from log_aggregator.models import Project, LogEntry, AnomalyAlert

class Command(BaseCommand):
    help = 'Detects anomalies in log ingestion (spikes in ERRORs)'

    def handle(self, *args, **options):
        now = timezone.now()
        five_mins_ago = now - timedelta(minutes=5)
        one_hour_ago = now - timedelta(hours=1)

        projects = Project.objects.all()
        for project in projects:
            # Historical errors in last 1 hour
            historical_errors = LogEntry.objects.filter(
                project=project,
                level='ERROR',
                timestamp__gte=one_hour_ago,
                timestamp__lt=five_mins_ago
            ).count()

            # Current errors in last 5 mins
            current_errors = LogEntry.objects.filter(
                project=project,
                level='ERROR',
                timestamp__gte=five_mins_ago
            ).count()

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
