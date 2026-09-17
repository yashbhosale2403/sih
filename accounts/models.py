import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    INVESTIGATING_OFFICER = 'INVESTIGATING_OFFICER', 'Investigating Officer'
    LEGAL_REVIEWER = 'LEGAL_REVIEWER', 'Legal Reviewer'
    VIEWER = 'VIEWER', 'Viewer'

class User(AbstractUser):
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.VIEWER)
    badge_id = models.CharField(max_length=32, unique=True)
    is_locked = models.BooleanField(default=False)
    failed_login_count = models.IntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} [{self.badge_id}] ({self.role})"

class CaseAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='case_assignments')
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'case')

    def __str__(self):
        return f"Assignment: {self.user.badge_id} -> Case {self.case.case_number} (active={self.active})"
