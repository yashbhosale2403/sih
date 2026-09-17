from rest_framework import serializers
from ledger.models import LedgerEntry
from accounts.serializers import UserSerializer
from documents.serializers import DocumentVersionSerializer

class LedgerEntrySerializer(serializers.ModelSerializer):
    actor_detail = UserSerializer(source='actor', read_only=True)
    document_version_detail = DocumentVersionSerializer(source='document_version', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = ['id', 'case', 'document_version', 'document_version_detail', 'action', 'actor', 'actor_detail', 'document_hash', 'prev_entry_hash', 'entry_hash', 'client_timestamp', 'server_timestamp']
        read_only_fields = fields
