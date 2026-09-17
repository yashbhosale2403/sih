import uuid
from django.db import models
from django.conf import settings

class LedgerAction(models.TextChoices):
    UPLOAD = 'UPLOAD', 'Upload'
    VIEW = 'VIEW', 'View'
    EDIT = 'EDIT', 'Edit'
    DOWNLOAD = 'DOWNLOAD', 'Download'
    REDACT = 'REDACT', 'Redact'
    DELETE_REQUEST = 'DELETE_REQUEST', 'Delete Request'
    SYNC = 'SYNC', 'Sync'

class LedgerEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.PROTECT, related_name='ledger_entries')
    document_version = models.ForeignKey(
        'documents.DocumentVersion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ledger_entries'
    )
    action = models.CharField(max_length=32, choices=LedgerAction.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ledger_actions')
    document_hash = models.CharField(max_length=64)
    prev_entry_hash = models.CharField(max_length=64, null=True, blank=True)
    entry_hash = models.CharField(max_length=64)
    client_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Ledger entries"
        ordering = ['server_timestamp']

    def save(self, *args, **kwargs):
        # Section 4: Override save() to raise an exception if pk already exists
        if self.pk and LedgerEntry.objects.filter(pk=self.pk).exists():
            raise PermissionError("Ledger entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Section 4: Immutability enforcement on delete
        raise PermissionError("Ledger entries are immutable and cannot be deleted.")

    def __str__(self):
        return f"LedgerEntry [{self.action}] Case:{self.case.case_number} Hash:{self.entry_hash[:8]}"
