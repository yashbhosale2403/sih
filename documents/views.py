import os
import mimetypes
from django.http import HttpResponse
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from documents.models import Document, DocumentVersion
from documents.serializers import DocumentSerializer, DocumentVersionSerializer
from documents.services import (
    compute_plaintext_sha256,
    encrypt_document_content,
    decrypt_document_content
)
from cases.models import Case
from accounts.models import User, UserRole, CaseAssignment
from accounts.permissions import can_access, get_client_ip
from ledger.models import LedgerEntry, LedgerAction
from ledger.services import compute_entry_hash
from alerts.models import AccessLog, AccessResult

def append_ledger_entry(case, document_version, action, actor, doc_hash):
    """
    Helper to create a LedgerEntry with correct prev_entry_hash and entry_hash computation.
    """
    latest = LedgerEntry.objects.filter(case=case).order_by('-server_timestamp').first()
    prev_hash = latest.entry_hash if latest else None

    entry = LedgerEntry(
        case=case,
        document_version=document_version,
        action=action,
        actor=actor,
        document_hash=doc_hash,
        prev_entry_hash=prev_hash,
        entry_hash="pending"
    )
    entry.save()

    real_hash = compute_entry_hash(
        doc_hash,
        prev_hash,
        action,
        actor.id,
        entry.server_timestamp,
        case.id
    )
    LedgerEntry.objects.filter(id=entry.id).update(entry_hash=real_hash)
    entry.entry_hash = real_hash
    return entry

class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Document.objects.none()

        case_id = self.request.query_params.get('case')
        if case_id:
            try:
                case = Case.objects.get(id=case_id)
                if can_access(user, case, action="LIST_DOCUMENTS", request=self.request):
                    return Document.objects.filter(case=case)
            except Case.DoesNotExist:
                return Document.objects.none()
            return Document.objects.none()

        if user.role == UserRole.ADMIN or user.is_superuser:
            return Document.objects.all()

        # Authorized users see documents for all cases assigned to them
        active_case_ids = CaseAssignment.objects.filter(user=user, active=True).values_list('case_id', flat=True)
        return Document.objects.filter(case_id__in=active_case_ids)

    def create(self, request, *args, **kwargs):
        case_id = request.data.get('case')
        title = request.data.get('title')
        doc_type = request.data.get('doc_type', 'OTHER')
        file_obj = request.FILES.get('file')

        if not case_id or not title or not file_obj:
            return Response({"detail": "case, title, and file are required fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            case = Case.objects.get(id=case_id)
        except Case.DoesNotExist:
            return Response({"detail": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

        if not can_access(request.user, case, action="UPLOAD_DOCUMENT", request=request):
            return Response({"detail": "Access denied to upload documents for this case."}, status=status.HTTP_403_FORBIDDEN)

        plaintext_bytes = file_obj.read()
        sha256_hash = compute_plaintext_sha256(plaintext_bytes)
        encrypted_bytes = encrypt_document_content(plaintext_bytes)

        orig_name = getattr(file_obj, 'name', '')
        _, ext = os.path.splitext(orig_name) if orig_name else ('', '')

        doc = Document.objects.create(
            case=case,
            title=title,
            doc_type=doc_type,
            original_filename=orig_name,
            file_extension=ext.lower(),
            created_by=request.user
        )

        version = DocumentVersion(
            document=doc,
            version_number=1,
            sha256_hash=sha256_hash,
            uploaded_by=request.user
        )
        file_name = f"doc_{doc.id}_v1.bin"
        version.encrypted_file.save(file_name, ContentFile(encrypted_bytes), save=True)

        doc.current_version = version
        doc.save()

        append_ledger_entry(case, version, LedgerAction.UPLOAD, request.user, sha256_hash)
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='new-version')
    def new_version(self, request, pk=None):
        doc = self.get_object()
        if not can_access(request.user, doc.case, action="NEW_DOCUMENT_VERSION", request=request):
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"detail": "file is required."}, status=status.HTTP_400_BAD_REQUEST)

        plaintext_bytes = file_obj.read()
        sha256_hash = compute_plaintext_sha256(plaintext_bytes)
        encrypted_bytes = encrypt_document_content(plaintext_bytes)

        next_version_num = (doc.current_version.version_number + 1) if doc.current_version else 1

        version = DocumentVersion(
            document=doc,
            version_number=next_version_num,
            sha256_hash=sha256_hash,
            uploaded_by=request.user
        )
        file_name = f"doc_{doc.id}_v{next_version_num}.bin"
        version.encrypted_file.save(file_name, ContentFile(encrypted_bytes), save=True)

        doc.current_version = version
        doc.save()

        append_ledger_entry(doc.case, version, LedgerAction.EDIT, request.user, sha256_hash)
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        user = request.user
        if not user or not user.is_authenticated:
            token_str = request.query_params.get('token')
            if token_str:
                try:
                    validated_token = AccessToken(token_str)
                    user_id = validated_token['user_id']
                    user = User.objects.get(id=user_id)
                except Exception:
                    return Response({"detail": "Invalid or expired token in query parameters."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user or not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        doc = self.get_object()
        if not can_access(user, doc.case, action="DOWNLOAD_DOCUMENT", request=request):
            return Response({"detail": "Access denied to download document."}, status=status.HTTP_403_FORBIDDEN)

        version_id = request.query_params.get('version_id')
        if version_id:
            try:
                version = DocumentVersion.objects.get(id=version_id, document=doc)
            except DocumentVersion.DoesNotExist:
                return Response({"detail": "Specified DocumentVersion not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            version = doc.current_version

        if not version or not version.encrypted_file:
            return Response({"detail": "No file version available."}, status=status.HTTP_404_NOT_FOUND)

        encrypted_bytes = version.encrypted_file.read()
        plaintext_bytes = decrypt_document_content(encrypted_bytes)

        ip = get_client_ip(request)
        AccessLog.objects.create(
            user=user,
            case=doc.case,
            action="DOWNLOAD",
            result=AccessResult.ALLOWED,
            ip_address=ip
        )

        append_ledger_entry(doc.case, version, LedgerAction.DOWNLOAD, user, version.sha256_hash)

        if doc.original_filename:
            download_name = doc.original_filename
        elif doc.file_extension:
            download_name = f"{doc.title.replace(' ', '_')}{doc.file_extension}"
        else:
            download_name = f"{doc.title.replace(' ', '_')}.bin"

        mime_type, _ = mimetypes.guess_type(download_name)
        if not mime_type:
            mime_type = 'application/octet-stream'

        response = HttpResponse(plaintext_bytes, content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{download_name}"'
        return response

    @action(detail=True, methods=['post'])
    def redact(self, request, pk=None):
        doc = self.get_object()
        if not can_access(request.user, doc.case, action="REDACT_DOCUMENT", request=request):
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        current = doc.current_version
        if not current:
            return Response({"detail": "No version to redact."}, status=status.HTTP_400_BAD_REQUEST)

        encrypted_bytes = current.encrypted_file.read()
        plaintext = decrypt_document_content(encrypted_bytes)
        redacted_plaintext = plaintext + b"\n[REDACTED SENSITIVE CONTENT]"
        new_sha256 = compute_plaintext_sha256(redacted_plaintext)
        new_encrypted = encrypt_document_content(redacted_plaintext)

        next_version_num = current.version_number + 1
        redacted_version = DocumentVersion(
            document=doc,
            version_number=next_version_num,
            sha256_hash=new_sha256,
            uploaded_by=request.user,
            is_redacted=True,
            redacted_from=current
        )
        file_name = f"doc_{doc.id}_v{next_version_num}_redacted.bin"
        redacted_version.encrypted_file.save(file_name, ContentFile(new_encrypted), save=True)

        doc.current_version = redacted_version
        doc.save()

        append_ledger_entry(doc.case, redacted_version, LedgerAction.REDACT, request.user, new_sha256)
        return Response(DocumentSerializer(doc).data)

    @action(detail=False, methods=['post'], url_path='(?P<version_id>[^/.]+)/simulate-tamper')
    def simulate_tamper(self, request, version_id=None):
        if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
            return Response({"detail": "Judge Demo Mode route requires ADMIN role."}, status=status.HTTP_403_FORBIDDEN)

        try:
            version = DocumentVersion.objects.get(id=version_id)
        except DocumentVersion.DoesNotExist:
            return Response({"detail": "DocumentVersion not found."}, status=status.HTTP_404_NOT_FOUND)

        version.sha256_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        version.save()

        return Response({
            "detail": f"SIMULATE TAMPER SUCCESS: DocumentVersion v{version.version_number} hash corrupted on disk.",
            "version_id": str(version.id),
            "tampered_sha256": version.sha256_hash
        })

    @action(detail=False, methods=['post'], url_path='(?P<version_id>[^/.]+)/restore-tamper')
    def restore_tamper(self, request, version_id=None):
        """
        Judge Demo Mode route: Restores a tampered DocumentVersion back to its valid original SHA-256 hash.
        """
        if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
            return Response({"detail": "Judge Demo Mode route requires ADMIN role."}, status=status.HTTP_403_FORBIDDEN)

        try:
            version = DocumentVersion.objects.get(id=version_id)
        except DocumentVersion.DoesNotExist:
            return Response({"detail": "DocumentVersion not found."}, status=status.HTTP_404_NOT_FOUND)

        encrypted_bytes = version.encrypted_file.read()
        plaintext_bytes = decrypt_document_content(encrypted_bytes)
        original_sha256 = compute_plaintext_sha256(plaintext_bytes)

        version.sha256_hash = original_sha256
        version.save()

        return Response({
            "detail": f"RESTORE TAMPER SUCCESS: DocumentVersion v{version.version_number} hash restored to valid SHA-256.",
            "version_id": str(version.id),
            "restored_sha256": version.sha256_hash
        })
