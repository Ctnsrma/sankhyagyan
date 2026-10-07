from django.contrib import admin

from .models import Chunk, Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "uploaded_by", "file_size", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "original_filename")
    readonly_fields = ("file_hash", "file_size", "original_filename", "created_at", "updated_at")


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "index", "section", "page_start", "page_end", "token_count")
    list_filter = ("document",)
    search_fields = ("text", "section")