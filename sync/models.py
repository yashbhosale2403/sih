import uuid
from django.db import models
from django.conf import settings

class SyncStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SYNCED = 'SYNCED', 'Synced'
    CONFLICT = 'CONFLICT', 'Conflict'

class OfflineAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_generated_id = models.UUIDField(unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offline_actions')
    document_version = models.ForeignKey(
        'documents.DocumentVersion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='offline_actions'
    )
    action = models.CharField(max_length=64)
    payload_hash = models.CharField(max_length=64)
    client_timestamp = models.DateTimeField()
    sync_status = models.CharField(max_length=16, choices=SyncStatus.choices, default=SyncStatus.PENDING)

    def __str__(self):
        return f"OfflineAction [{self.sync_status}] ClientID:{self.client_generated_id}"
