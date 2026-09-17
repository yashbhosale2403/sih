import os
import sys
import django

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securedocs.settings')
django.setup()

from accounts.models import User, UserRole, CaseAssignment
from cases.models import Case, CaseStatus
from documents.models import Document, DocumentVersion, DocumentType
from documents.services import compute_plaintext_sha256, encrypt_document_content
from documents.views import append_ledger_entry
from ledger.models import LedgerAction
from alerts.models import AccessLog, AccessResult, Alert, AlertType, AlertSeverity
from django.core.files.base import ContentFile

def seed():
    print("[SEED] Seeding demo data...")

    # 1. Create Users
    admin, _ = User.objects.get_or_create(
        username="test_admin",
        defaults={
            "badge_id": "BADGE-ADMIN-001",
            "role": UserRole.ADMIN,
            "is_staff": True,
            "is_superuser": True
        }
    )
    admin.set_password("AdminPassword123!")
    admin.save()

    officer, _ = User.objects.get_or_create(
        username="officer_sharma",
        defaults={
            "badge_id": "BADGE-POLICE-101",
            "role": UserRole.INVESTIGATING_OFFICER
        }
    )
    officer.set_password("OfficerPass123!")
    officer.save()

    reviewer, _ = User.objects.get_or_create(
        username="reviewer_mehta",
        defaults={
            "badge_id": "BADGE-LEGAL-202",
            "role": UserRole.LEGAL_REVIEWER
        }
    )
    reviewer.set_password("ReviewerPass123!")
    reviewer.save()

    # 2. Create Case
    case, _ = Case.objects.get_or_create(
        case_number="FIR/2026/00123",
        defaults={
            "title": "Cyber Crime Investigation - Bank Fraud",
            "status": CaseStatus.OPEN,
            "created_by": admin
        }
    )

    CaseAssignment.objects.get_or_create(user=officer, case=case, defaults={"active": True})
    CaseAssignment.objects.get_or_create(user=reviewer, case=case, defaults={"active": True})

    # 3. Create Documents
    doc1, _ = Document.objects.get_or_create(
        case=case,
        title="First Information Report (FIR)",
        defaults={
            "doc_type": DocumentType.FIR,
            "created_by": officer
        }
    )
    if not doc1.current_version:
        content = b"OFFICIAL FIR REPORT: Case FIR/2026/00123. Cyber crime incident reported on 16 Sep 2026."
        sha = compute_plaintext_sha256(content)
        enc = encrypt_document_content(content)
        v1 = DocumentVersion(document=doc1, version_number=1, sha256_hash=sha, uploaded_by=officer)
        v1.encrypted_file.save("fir_2026_00123_v1.bin", ContentFile(enc), save=True)
        doc1.current_version = v1
        doc1.save()
        append_ledger_entry(case, v1, LedgerAction.UPLOAD, officer, sha)

    doc2, _ = Document.objects.get_or_create(
        case=case,
        title="Forensic Disk Image Inspection",
        defaults={
            "doc_type": DocumentType.FORENSIC_REPORT,
            "created_by": officer
        }
    )
    if not doc2.current_version:
        content2 = b"FORENSIC DISK REPORT: Hash verified SHA-256 for hard drive serial #HD-884920."
        sha2 = compute_plaintext_sha256(content2)
        enc2 = encrypt_document_content(content2)
        v2 = DocumentVersion(document=doc2, version_number=1, sha256_hash=sha2, uploaded_by=officer)
        v2.encrypted_file.save("forensic_hd_v1.bin", ContentFile(enc2), save=True)
        doc2.current_version = v2
        doc2.save()
        append_ledger_entry(case, v2, LedgerAction.UPLOAD, officer, sha2)

    # 4. Create Sample AccessLog & Alert
    log, _ = AccessLog.objects.get_or_create(
        user=officer,
        case=case,
        action="DOWNLOAD",
        result=AccessResult.ALLOWED,
        ip_address="127.0.0.1"
    )

    Alert.objects.get_or_create(
        user=officer,
        case=case,
        alert_type=AlertType.OFF_HOURS_ACCESS,
        defaults={
            "severity": AlertSeverity.MEDIUM,
            "description": "User officer_sharma accessed case FIR/2026/00123 outside allowed shift hours."
        }
    )

    print("[SEED] Demo data successfully seeded!")

if __name__ == "__main__":
    seed()
