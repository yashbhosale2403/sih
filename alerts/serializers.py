from rest_framework import serializers
from alerts.models import AccessLog, Alert
from accounts.serializers import UserSerializer

class AccessLogSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    class Meta:
        model = AccessLog
        fields = ['id', 'user', 'user_detail', 'case', 'action', 'result', 'ip_address', 'timestamp']

class AlertSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    resolved_by_detail = UserSerializer(source='resolved_by', read_only=True)
    triggering_logs_detail = AccessLogSerializer(source='triggering_logs', many=True, read_only=True)

    class Meta:
        model = Alert
        fields = ['id', 'alert_type', 'severity', 'user', 'user_detail', 'case', 'description', 'status', 'triggering_logs', 'triggering_logs_detail', 'created_at', 'resolved_by', 'resolved_by_detail', 'resolved_at']
