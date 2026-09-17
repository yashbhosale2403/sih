from rest_framework import serializers
from sync.models import OfflineAction
from accounts.serializers import UserSerializer

class OfflineActionSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    class Meta:
        model = OfflineAction
        fields = ['id', 'client_generated_id', 'user', 'user_detail', 'document_version', 'action', 'payload_hash', 'client_timestamp', 'sync_status']
