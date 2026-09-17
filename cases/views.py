from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from cases.models import Case
from cases.serializers import CaseSerializer
from accounts.models import UserRole, CaseAssignment
from accounts.permissions import can_access
from ledger.models import LedgerEntry
from ledger.serializers import LedgerEntrySerializer
from ledger.services import verify_case_integrity
from alerts.models import Alert
from alerts.serializers import AlertSerializer
from audit.services import generate_case_audit_pdf

class CaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Case.objects.none()

        if user.role == UserRole.ADMIN or user.is_superuser:
            return Case.objects.all()

        active_assignments = CaseAssignment.objects.filter(user=user, active=True).values_list('case_id', flat=True)
        queryset = Case.objects.filter(id__in=active_assignments)

        # Police Officers and Forensic viewers do NOT see CLOSED cases
        if user.role in [UserRole.INVESTIGATING_OFFICER, UserRole.VIEWER]:
            queryset = queryset.exclude(status="CLOSED")

        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.role not in [UserRole.ADMIN, UserRole.INVESTIGATING_OFFICER] and not request.user.is_superuser:
            return Response({"detail": "Only Police Officers and SOC Analysts can create new cases."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = serializer.save(created_by=request.user)

        # Auto-assign active investigating officers and legal reviewers
        from accounts.models import User
        active_users = User.objects.filter(role__in=[UserRole.INVESTIGATING_OFFICER, UserRole.LEGAL_REVIEWER])
        for u in active_users:
            CaseAssignment.objects.get_or_create(user=u, case=case, defaults={'active': True})
        CaseAssignment.objects.get_or_create(user=request.user, case=case, defaults={'active': True})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        case = self.get_object()
        if request.user.role not in [UserRole.LEGAL_REVIEWER, UserRole.ADMIN] and not request.user.is_superuser:
            return Response({"detail": "Only Court Judges and Admins can close cases."}, status=status.HTTP_403_FORBIDDEN)
        
        from cases.models import CaseStatus
        case.status = CaseStatus.CLOSED
        case.save()

        from documents.views import append_ledger_entry
        append_ledger_entry(case, None, "CASE_CLOSED", request.user, "0" * 64)

        return Response(CaseSerializer(case).data)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        case = self.get_object()
        if request.user.role not in [UserRole.LEGAL_REVIEWER, UserRole.ADMIN] and not request.user.is_superuser:
            return Response({"detail": "Only Court Judges and Admins can reopen cases."}, status=status.HTTP_403_FORBIDDEN)
        
        from cases.models import CaseStatus
        case.status = CaseStatus.OPEN
        case.save()

        from documents.views import append_ledger_entry
        append_ledger_entry(case, None, "CASE_REOPENED", request.user, "0" * 64)

        return Response(CaseSerializer(case).data)

    def retrieve(self, request, *args, **kwargs):
        case = self.get_object()
        if not can_access(request.user, case, action="VIEW_CASE", request=request):
            return Response({"detail": "Access denied to this case."}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        case = self.get_object()
        if not can_access(request.user, case, action="VERIFY_CASE", request=request):
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)
        result = verify_case_integrity(case.id)
        return Response(result)

    @action(detail=True, methods=['get'], url_path='audit-timeline')
    def audit_timeline(self, request, pk=None):
        case = self.get_object()
        if not can_access(request.user, case, action="VIEW_AUDIT_TIMELINE", request=request):
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        entries = LedgerEntry.objects.filter(case=case).order_by('server_timestamp')
        alerts = Alert.objects.filter(case=case).order_by('created_at')
        verification = verify_case_integrity(case.id)

        return Response({
            "case_id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "verification": verification,
            "timeline": LedgerEntrySerializer(entries, many=True).data,
            "alerts": AlertSerializer(alerts, many=True).data
        })

    @action(detail=True, methods=['get'], url_path='audit-report.pdf')
    def audit_report_pdf(self, request, pk=None):
        case = self.get_object()
        if not can_access(request.user, case, action="EXPORT_AUDIT_PDF", request=request):
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        pdf_bytes = generate_case_audit_pdf(str(case.id))
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="AuditReport_{case.case_number.replace("/", "_")}.pdf"'
        return response
