from rest_framework import parsers, viewsets

from .models import Document
from .permissions import IsTrainingAdminOrReadOnly
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("uploaded_by")
    serializer_class = DocumentSerializer
    permission_classes = [IsTrainingAdminOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()