import hashlib
from pathlib import Path

from rest_framework import serializers

from .models import Chunk, Document

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def compute_sha256(uploaded_file):
    hasher = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        hasher.update(chunk)
    uploaded_file.seek(0)
    return hasher.hexdigest()


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id", "title", "description", "file", "original_filename",
            "file_size", "status", "error_message", "page_count",
            "uploaded_by", "created_at",
        ]
        read_only_fields = [
            "original_filename", "file_size", "status",
            "error_message", "page_count", "created_at",
        ]

    def validate_file(self, file):
        if Path(file.name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("Only PDF files are supported right now.")
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("File is too large. Maximum size is 25 MB.")
        header = file.read(5)
        file.seek(0)
        if header != b"%PDF-":
            raise serializers.ValidationError("This file is not a valid PDF.")
        return file

    def validate(self, attrs):
        file = attrs["file"]
        file_hash = compute_sha256(file)
        if Document.objects.filter(file_hash=file_hash).exists():
            raise serializers.ValidationError(
                {"file": "This document has already been uploaded."}
            )
        attrs["file_hash"] = file_hash
        attrs["original_filename"] = file.name
        attrs["file_size"] = file.size
        return attrs

class ChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chunk
        fields = ["id", "index", "section", "page_start", "page_end", "token_count", "text"]