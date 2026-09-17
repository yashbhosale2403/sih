from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sync.models import OfflineAction, SyncStatus
from sync.serializers import OfflineActionSerializer
from documents.models import DocumentVersion
from accounts.models import UserRole
from ledger.models import LedgerAction
from documents.views import append_ledger_entry

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_push_view(request):
    """
    Section 7 Protocol:
    POST /api/sync/push/ accepts array of OfflineAction payloads.
    1. Idempotent check against client_generated_id.
    2. Check base version vs current version for conflict detection.
    """
    actions_data = request.data.get('actions', [])
    if not isinstance(actions_data, list):
        return Response({"detail": "actions must be a list."}, status=status.HTTP_400_BAD_REQUEST)

    results = []
    for item in actions_data:
        client_id = item.get('client_generated_id')
        action_type = item.get('action')
        doc_version_id = item.get('document_version_id')
        payload_hash = item.get('payload_hash', '')
        client_ts = item.get('client_timestamp')

        if not client_id or not action_type or not client_ts:
            continue

        # Idempotency check
        existing = OfflineAction.objects.filter(client_generated_id=client_id).first()
        if existing:
            results.append(OfflineActionSerializer(existing).data)
            continue

        doc_version = None
        if doc_version_id:
            doc_version = DocumentVersion.objects.filter(id=doc_version_id).first()

        # Check for conflict on EDIT/ANNOTATE
        sync_status = SyncStatus.SYNCED
        if doc_version and action_type in ['EDIT', 'ANNOTATE']:
            document = doc_version.document
            if document.current_version and document.current_version.id != doc_version.id:
                sync_status = SyncStatus.CONFLICT

        offline_action = OfflineAction.objects.create(
            client_generated_id=client_id,
            user=request.user,
            document_version=doc_version,
            action=action_type,
            payload_hash=payload_hash,
            client_timestamp=client_ts,
            sync_status=sync_status
        )

        if sync_status == SyncStatus.SYNCED and doc_version:
            append_ledger_entry(
                doc_version.document.case,
                doc_version,
                LedgerAction.SYNC,
                request.user,
                payload_hash or doc_version.sha256_hash
            )

        results.append(OfflineActionSerializer(offline_action).data)

    return Response({"synced_actions": results})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_conflicts_view(request):
    conflicts = OfflineAction.objects.filter(sync_status=SyncStatus.CONFLICT)
    return Response(OfflineActionSerializer(conflicts, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_conflict_view(request, conflict_id):
    if request.user.role not in [UserRole.ADMIN, UserRole.LEGAL_REVIEWER] and not request.user.is_superuser:
        return Response({"detail": "Permission denied. ADMIN or LEGAL_REVIEWER required."}, status=status.HTTP_403_FORBIDDEN)

    try:
        conflict = OfflineAction.objects.get(id=conflict_id, sync_status=SyncStatus.CONFLICT)
    except OfflineAction.DoesNotExist:
        return Response({"detail": "Conflict not found."}, status=status.HTTP_404_NOT_FOUND)

    resolution_choice = request.data.get('choice', 'SERVER_CURRENT')
    conflict.sync_status = SyncStatus.SYNCED
    conflict.save()

    if conflict.document_version:
        append_ledger_entry(
            conflict.document_version.document.case,
            conflict.document_version,
            LedgerAction.SYNC,
            request.user,
            conflict.payload_hash
        )

    return Response({"detail": f"Conflict resolved using {resolution_choice}.", "action": OfflineActionSerializer(conflict).data})
