import uuid
from django.db import models
from django.conf import settings

class CaseStatus(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    CLOSED = 'CLOSED', 'Closed'
    ARCHIVED = 'ARCHIVED', 'Archived'

class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=CaseStatus.choices, default=CaseStatus.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_cases')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.case_number} - {self.title} ({self.status})"
