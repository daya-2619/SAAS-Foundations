import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="log_projects")
    name = models.CharField(max_length=255)
    api_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class LogEntry(models.Model):
    LEVEL_CHOICES = (
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARN', 'WARN'),
        ('ERROR', 'ERROR'),
        ('FATAL', 'FATAL'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="logs")
    timestamp = models.DateTimeField(db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    message = models.TextField()
    raw_data = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['project', 'timestamp']),
            models.Index(fields=['project', 'level', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.level}] {self.timestamp} - {self.message[:50]}"

class AnomalyAlert(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="alerts")
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.project.name} Alert - {self.timestamp}"
