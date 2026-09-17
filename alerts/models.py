import uuid
from django.db import models
from django.conf import settings

class AccessResult(models.TextChoices):
    ALLOWED = 'ALLOWED', 'Allowed'
    DENIED = 'DENIED', 'Denied'

class AccessLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='access_logs')
    case = models.ForeignKey('cases.Case', null=True, blank=True, on_delete=models.SET_NULL, related_name='access_logs')
    action = models.CharField(max_length=64)
    result = models.CharField(max_length=16, choices=AccessResult.choices)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AccessLog [{self.result}] User:{self.user.username} Action:{self.action}"

class AlertType(models.TextChoices):
    BULK_DOWNLOAD = 'BULK_DOWNLOAD', 'Bulk Download'
    OFF_HOURS_ACCESS = 'OFF_HOURS_ACCESS', 'Off Hours Access'
    UNAUTHORIZED_ATTEMPTS = 'UNAUTHORIZED_ATTEMPTS', 'Unauthorized Attempts'
    FAILED_LOGIN_LOCKOUT = 'FAILED_LOGIN_LOCKOUT', 'Failed Login Lockout'

class AlertSeverity(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'

class AlertStatus(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
    RESOLVED = 'RESOLVED', 'Resolved'

class Alert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=32, choices=AlertType.choices)
    severity = models.CharField(max_length=16, choices=AlertSeverity.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    case = models.ForeignKey('cases.Case', null=True, blank=True, on_delete=models.SET_NULL, related_name='alerts')
    description = models.TextField()
    status = models.CharField(max_length=16, choices=AlertStatus.choices, default=AlertStatus.OPEN)
    triggering_logs = models.ManyToManyField(AccessLog, blank=True, related_name='triggered_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alert [{self.severity}] {self.alert_type} - {self.user.username}"
