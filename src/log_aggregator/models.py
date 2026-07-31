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



class AnomalyAlert(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="alerts")
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.project.name} Alert - {self.timestamp}"
