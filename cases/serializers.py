from rest_framework import serializers
from cases.models import Case
from accounts.serializers import UserSerializer

class CaseSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = ['id', 'case_number', 'title', 'status', 'created_by', 'created_by_detail', 'document_count', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def get_document_count(self, obj):
        return obj.documents.count()
