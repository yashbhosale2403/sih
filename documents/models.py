import uuid
from django.db import models
from django.conf import settings

class DocumentType(models.TextChoices):
    FIR = 'FIR', 'FIR'
    CHARGESHEET = 'CHARGESHEET', 'Chargesheet'
    FORENSIC_REPORT = 'FORENSIC_REPORT', 'Forensic Report'
    WITNESS_STATEMENT = 'WITNESS_STATEMENT', 'Witness Statement'
    EVIDENCE = 'EVIDENCE', 'Evidence'
    OTHER = 'OTHER', 'Other'

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=32, choices=DocumentType.choices, default=DocumentType.OTHER)
    current_version = models.ForeignKey(
        'DocumentVersion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='current_for_documents'
    )
    original_filename = models.CharField(max_length=255, blank=True, default='')
    file_extension = models.CharField(max_length=32, blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_documents')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.doc_type})"

class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    encrypted_file = models.FileField(upload_to='encrypted_docs/')
    sha256_hash = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='uploaded_versions')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_redacted = models.BooleanField(default=False)
    redacted_from = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='redacted_versions'
    )

    class Meta:
        unique_together = ('document', 'version_number')

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"
