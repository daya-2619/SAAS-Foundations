from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from log_aggregator.models import Project, AnomalyAlert
from log_aggregator.clickhouse_client import get_client
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_anomaly_detection():
    logger.info("Running automated anomaly detection...")
    now = timezone.now()
    five_mins_ago = now - timedelta(minutes=5)
    one_hour_ago = now - timedelta(hours=1)

    projects = Project.objects.all()
    
    ch_client = get_client()
    if not ch_client:
        logger.error("Failed to connect to ClickHouse for anomaly detection")
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

        baseline_avg_per_5_min = historical_errors / 11.0 if historical_errors > 0 else 0

        # Simple anomaly threshold
        if current_errors > 5 and current_errors > (baseline_avg_per_5_min * 3):
            alert_msg = f"Spike in ERRORs detected! {current_errors} in last 5 mins (Baseline: {baseline_avg_per_5_min:.1f})"
            AnomalyAlert.objects.create(
                project=project,
                description=alert_msg
            )
            logger.warning(f"[{project.name}] {alert_msg}")
            
            # Send Email Alert
            if project.user and project.user.email:
                try:
                    send_mail(
                        subject=f"URGENT: Anomaly Detected in {project.name}",
                        message=f"Hello,\n\nOur systems have detected an anomaly in your project '{project.name}'.\n\nDetails: {alert_msg}\n\nPlease check your dashboard immediately.",
                        from_email=None,
                        recipient_list=[project.user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send email alert: {e}")
        else:
            logger.info(f"[{project.name}] Normal. {current_errors} errors.")
