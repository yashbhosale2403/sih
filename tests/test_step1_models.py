import pytest
from django.db import IntegrityError
from accounts.models import User, UserRole, CaseAssignment
from cases.models import Case, CaseStatus
from documents.models import Document, DocumentVersion, DocumentType
from ledger.models import LedgerEntry, LedgerAction
from alerts.models import AccessLog, AccessResult, Alert, AlertType, AlertSeverity
from sync.models import OfflineAction, SyncStatus
import uuid
from django.utils import timezone

@pytest.mark.django_db
def test_user_and_roles():
    user = User.objects.create_user(
        username="officer_sharma",
        password="securepass123",
        badge_id="BADGE-101",
        role=UserRole.INVESTIGATING_OFFICER
    )
    assert user.badge_id == "BADGE-101"
    assert user.role == UserRole.INVESTIGATING_OFFICER
    assert not user.is_locked
    assert user.failed_login_count == 0

@pytest.mark.django_db
def test_case_creation_and_assignment():
    admin = User.objects.create_user(username="admin_user", badge_id="BADGE-001", role=UserRole.ADMIN)
    officer = User.objects.create_user(username="officer1", badge_id="BADGE-002", role=UserRole.INVESTIGATING_OFFICER)

    case = Case.objects.create(
        case_number="FIR/2026/00123",
        title="Cyber Fraud Investigation",
        created_by=admin
    )
    assert case.status == CaseStatus.OPEN

    assignment = CaseAssignment.objects.create(user=officer, case=case, active=True)
    assert assignment.active
    assert assignment.user == officer
    assert assignment.case == case

@pytest.mark.django_db
def test_document_and_versioning():
    officer = User.objects.create_user(username="officer2", badge_id="BADGE-003", role=UserRole.INVESTIGATING_OFFICER)
    case = Case.objects.create(case_number="FIR/2026/00124", title="Forensic Analysis", created_by=officer)

    doc = Document.objects.create(case=case, title="Forensic Disk Image Log", doc_type=DocumentType.FORENSIC_REPORT, created_by=officer)
    version = DocumentVersion.objects.create(
        document=doc,
        version_number=1,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        uploaded_by=officer
    )
    doc.current_version = version
    doc.save()

    assert doc.current_version.version_number == 1
    assert doc.doc_type == DocumentType.FORENSIC_REPORT

@pytest.mark.django_db
def test_ledger_entry_cannot_be_updated_or_deleted():
    """Requirement section 9: test_ledger_entry_cannot_be_updated_or_deleted"""
    officer = User.objects.create_user(username="officer3", badge_id="BADGE-004", role=UserRole.INVESTIGATING_OFFICER)
    case = Case.objects.create(case_number="FIR/2026/00125", title="Evidence Logging", created_by=officer)

    entry = LedgerEntry.objects.create(
        case=case,
        action=LedgerAction.UPLOAD,
        actor=officer,
        document_hash="a" * 64,
        prev_entry_hash="0" * 64,
        entry_hash="b" * 64
    )
    assert entry.pk is not None

    # Test update prevention
    with pytest.raises(PermissionError) as excinfo:
        entry.action = LedgerAction.EDIT
        entry.save()
    assert "immutable and cannot be updated" in str(excinfo.value)

    # Test delete prevention
    with pytest.raises(PermissionError) as excinfo_del:
        entry.delete()
    assert "immutable and cannot be deleted" in str(excinfo_del.value)

@pytest.mark.django_db
def test_accesslog_and_alert():
    officer = User.objects.create_user(username="officer4", badge_id="BADGE-005", role=UserRole.INVESTIGATING_OFFICER)
    case = Case.objects.create(case_number="FIR/2026/00126", title="Access Log Test", created_by=officer)

    log = AccessLog.objects.create(
        user=officer,
        case=case,
        action="VIEW",
        result=AccessResult.ALLOWED,
        ip_address="127.0.0.1"
    )
    assert log.result == AccessResult.ALLOWED

    alert = Alert.objects.create(
        alert_type=AlertType.UNAUTHORIZED_ATTEMPTS,
        severity=AlertSeverity.HIGH,
        user=officer,
        case=case,
        description="Multiple denied attempts"
    )
    alert.triggering_logs.add(log)
    assert alert.triggering_logs.count() == 1

@pytest.mark.django_db
def test_offline_action_dedup():
    officer = User.objects.create_user(username="officer5", badge_id="BADGE-006", role=UserRole.INVESTIGATING_OFFICER)
    client_id = uuid.uuid4()

    action1 = OfflineAction.objects.create(
        client_generated_id=client_id,
        user=officer,
        action="VIEW",
        payload_hash="c" * 64,
        client_timestamp=timezone.now()
    )
    assert action1.sync_status == SyncStatus.PENDING

    with pytest.raises(IntegrityError):
        OfflineAction.objects.create(
            client_generated_id=client_id,
            user=officer,
            action="VIEW",
            payload_hash="c" * 64,
            client_timestamp=timezone.now()
        )

@pytest.mark.django_db
def test_document_access_control():
    from accounts.permissions import can_access
    admin = User.objects.create_user(username="admin_test", badge_id="BADGE-A01", role=UserRole.ADMIN)
    assigned_officer = User.objects.create_user(username="assigned_officer", badge_id="BADGE-P01", role=UserRole.INVESTIGATING_OFFICER)
    unassigned_officer = User.objects.create_user(username="unassigned_officer", badge_id="BADGE-P02", role=UserRole.INVESTIGATING_OFFICER)

    case = Case.objects.create(case_number="FIR/2026/99999", title="Confidential Investigation", created_by=admin)
    doc = Document.objects.create(case=case, title="Confidential Report", doc_type=DocumentType.EVIDENCE, created_by=admin)
    CaseAssignment.objects.create(user=assigned_officer, case=case, active=True)

    # 1. Assigned officer CAN access case and documents
    assert can_access(assigned_officer, case, action="LIST_DOCUMENTS") is True

    # 2. Unassigned officer CANNOT access case or documents
    assert can_access(unassigned_officer, case, action="LIST_DOCUMENTS") is False

    # 3. Admin CAN access all cases and documents
    assert can_access(admin, case, action="LIST_DOCUMENTS") is True

