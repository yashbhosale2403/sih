from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from alerts.models import Alert, AlertStatus
from alerts.serializers import AlertSerializer
from accounts.models import UserRole

class AlertViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertSerializer

    def get_queryset(self):
        user = self.request.user
        # Strict RBAC: Only ADMIN role / SOC Analysts can access SOC Anomaly Alerts (Section 5 & 6)
        if user.role != UserRole.ADMIN and not user.is_superuser:
            return Alert.objects.none()

        queryset = Alert.objects.all()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        severity_param = self.request.query_params.get('severity')
        if severity_param:
            queryset = queryset.filter(severity=severity_param)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
            return Response({"detail": "Access denied. SOC Alerts Dashboard is restricted to SOC Security Analysts (ADMIN)."}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
            return Response({"detail": "Access denied. Only SOC Analysts can acknowledge alerts."}, status=status.HTTP_403_FORBIDDEN)
        alert = self.get_object()
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.save()
        return Response(AlertSerializer(alert).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
            return Response({"detail": "Access denied. Only SOC Analysts can resolve alerts."}, status=status.HTTP_403_FORBIDDEN)
        alert = self.get_object()
        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save()
        return Response(AlertSerializer(alert).data)

    @action(detail=True, methods=['post'])
    def unresolve(self, request, pk=None):
        if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
            return Response({"detail": "Access denied. Only SOC Analysts can unresolve alerts."}, status=status.HTTP_403_FORBIDDEN)
        alert = self.get_object()
        alert.status = AlertStatus.OPEN
        alert.resolved_by = None
        alert.resolved_at = None
        alert.save()
        return Response(AlertSerializer(alert).data)
