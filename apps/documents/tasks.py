import logging

from celery import shared_task
from django.db import transaction

from .models import Chunk, Document
from .services.chunking import chunk_pages
from .services.extraction import extract_pages

logger = logging.getLogger(__name__)


@shared_task
def process_document(document_id):
    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        logger.warning("Document %s no longer exists, skipping.", document_id)
        return

    if document.status == Document.Status.PROCESSED:
        logger.info("Document %s already processed, skipping.", document_id)
        return

    document.status = Document.Status.PROCESSING
    document.error_message = ""
    document.save(update_fields=["status", "error_message", "updated_at"])

    try:
        pages = extract_pages(document.file.path)
        if not any(page["text"] for page in pages):
            raise ValueError(
                "No extractable text found. This may be a scanned PDF (OCR is not supported yet)."
            )

        chunks = chunk_pages(pages)

        with transaction.atomic():
            document.chunks.all().delete()
            Chunk.objects.bulk_create([
                Chunk(
                    document=document,
                    index=i,
                    text=c.text,
                    section=c.section[:500],
                    page_start=c.page_start,
                    page_end=c.page_end,
                    token_count=c.token_count,
                    content_hash=c.content_hash,
                )
                for i, c in enumerate(chunks)
            ])
            document.page_count = len(pages)
            document.status = Document.Status.PROCESSED
            document.save(update_fields=["page_count", "status", "updated_at"])

        logger.info("Processed document %s: %d pages, %d chunks", document_id, len(pages), len(chunks))

    except Exception as exc:
        logger.exception("Failed to process document %s", document_id)
        document.status = Document.Status.FAILED
        document.error_message = str(exc)[:2000]
        document.save(update_fields=["status", "error_message", "updated_at"])
        raise