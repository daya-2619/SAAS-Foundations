from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from log_aggregator.models import Project, LogEntry, AnomalyAlert
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_anomaly_detection():
    logger.info("Running automated anomaly detection...")
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
