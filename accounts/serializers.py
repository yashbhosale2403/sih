from rest_framework import serializers
from accounts.models import User, CaseAssignment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'badge_id', 'role', 'is_locked', 'failed_login_count', 'last_login_ip']

class CaseAssignmentSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    class Meta:
        model = CaseAssignment
        fields = ['id', 'user', 'case', 'assigned_at', 'active', 'user_detail']
