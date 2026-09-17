import hashlib
from ledger.models import LedgerEntry
from cases.models import Case
from documents.models import Document

def compute_entry_hash(document_hash, prev_entry_hash, action, actor_id, server_timestamp, case_id):
    """
    Computes entry_hash = SHA256(document_hash + prev_entry_hash + action + str(actor_id) + server_timestamp.isoformat() + str(case_id))
    """
    prev_hash = prev_entry_hash or ("0" * 64)
    ts_str = server_timestamp.isoformat() if hasattr(server_timestamp, 'isoformat') else str(server_timestamp)
    raw = f"{document_hash}{prev_hash}{action}{actor_id}{ts_str}{case_id}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def verify_case_integrity(case_id) -> dict:
    """
    Section 4 verification algorithm:
    1. Fetch all LedgerEntry rows for case ordered by server_timestamp.
    2. Walk genesis forward: recompute entry_hash, compare to stored.
    3. Recompute document_hash for CURRENT DocumentVersion of each document, compare to hash of most recent relevant LedgerEntry.
    4. Return structured VerificationResult dict.
    """
    try:
        case = Case.objects.get(id=case_id)
    except Case.DoesNotExist:
        return {
            "case_id": str(case_id),
            "verified": False,
            "total_entries": 0,
            "first_break_at_entry_id": None,
            "broken_reason": "case_not_found"
        }

    entries = list(LedgerEntry.objects.filter(case=case).order_by('server_timestamp'))
    if not entries:
        return {
            "case_id": str(case.id),
            "verified": True,
            "total_entries": 0,
            "first_break_at_entry_id": None,
            "broken_reason": None
        }

    expected_prev = "0" * 64
    for entry in entries:
        computed_hash = compute_entry_hash(
            entry.document_hash,
            entry.prev_entry_hash,
            entry.action,
            entry.actor.id,
            entry.server_timestamp,
            case.id
        )

        # 1. Verify Merkle hash chain integrity
        if computed_hash != entry.entry_hash:
            return {
                "case_id": str(case.id),
                "verified": False,
                "total_entries": len(entries),
                "first_break_at_entry_id": str(entry.id),
                "broken_reason": "entry_hash_mismatch"
            }

        # Verify prev_entry_hash matches expected chain linkage
        if (entry.prev_entry_hash or ("0" * 64)) != expected_prev:
            return {
                "case_id": str(case.id),
                "verified": False,
                "total_entries": len(entries),
                "first_break_at_entry_id": str(entry.id),
                "broken_reason": "prev_entry_hash_mismatch"
            }

        expected_prev = entry.entry_hash

    # 2. Check current document version hashes against latest ledger entry hash
    documents = Document.objects.filter(case=case)
    for doc in documents:
        if doc.current_version:
            latest_ledger = LedgerEntry.objects.filter(
                case=case,
                document_version=doc.current_version
            ).order_by('-server_timestamp').first()

            if latest_ledger:
                if latest_ledger.document_hash != doc.current_version.sha256_hash:
                    return {
                        "case_id": str(case.id),
                        "verified": False,
                        "total_entries": len(entries),
                        "first_break_at_entry_id": str(latest_ledger.id),
                        "broken_reason": "document_hash_mismatch"
                    }

    return {
        "case_id": str(case.id),
        "verified": True,
        "total_entries": len(entries),
        "first_break_at_entry_id": None,
        "broken_reason": None
    }
