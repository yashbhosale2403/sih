from rest_framework import serializers
from documents.models import Document, DocumentVersion
from accounts.serializers import UserSerializer

class DocumentVersionSerializer(serializers.ModelSerializer):
    uploaded_by_detail = UserSerializer(source='uploaded_by', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    document_id = serializers.UUIDField(source='document.id', read_only=True)
    original_filename = serializers.CharField(source='document.original_filename', read_only=True)
    file_extension = serializers.CharField(source='document.file_extension', read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'document_id', 'document_title', 'original_filename', 'file_extension', 'version_number', 'encrypted_file', 'sha256_hash', 'uploaded_by', 'uploaded_by_detail', 'uploaded_at', 'is_redacted', 'redacted_from']
        read_only_fields = ['sha256_hash', 'uploaded_by', 'uploaded_at']

class DocumentSerializer(serializers.ModelSerializer):
    current_version_detail = DocumentVersionSerializer(source='current_version', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'case', 'title', 'doc_type', 'original_filename', 'file_extension', 'current_version', 'current_version_detail', 'created_by', 'created_by_detail', 'created_at']
        read_only_fields = ['created_by', 'created_at']
