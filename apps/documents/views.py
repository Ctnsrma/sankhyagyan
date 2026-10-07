from django.db import transaction
from rest_framework import parsers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Document
from .permissions import IsTrainingAdminOrReadOnly
from .serializers import ChunkSerializer, DocumentSerializer
from .tasks import process_document


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("uploaded_by")
    serializer_class = DocumentSerializer
    permission_classes = [IsTrainingAdminOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_create(self, serializer):
        document = serializer.save(uploaded_by=self.request.user)
        transaction.on_commit(lambda: process_document.delay(document.id))

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()

    @action(detail=True, methods=["post"])
    def reprocess(self, request, pk=None):
        document = self.get_object()
        document.status = Document.Status.UPLOADED
        document.error_message = ""
        document.save(update_fields=["status", "error_message", "updated_at"])
        transaction.on_commit(lambda: process_document.delay(document.id))
        return Response({"detail": "Reprocessing started."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def chunks(self, request, pk=None):
        document = self.get_object()
        return Response(ChunkSerializer(document.chunks.all(), many=True).data)