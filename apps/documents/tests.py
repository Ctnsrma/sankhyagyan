import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Document

TEMP_MEDIA = tempfile.mkdtemp()
FAKE_PDF = b"%PDF-1.4\n%test content\n%%EOF"


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DocumentUploadTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.admin = User.objects.create_user("admin1", password="pass12345", role=User.Role.ADMIN)
        self.learner = User.objects.create_user("learner1", password="pass12345")
        self.url = "/api/documents/"

    def upload(self, content=FAKE_PDF, name="manual.pdf"):
        file = SimpleUploadedFile(name, content, content_type="application/pdf")
        return self.client.post(self.url, {"title": "Test Manual", "file": file}, format="multipart")

    def test_admin_can_upload_pdf(self):
        self.client.force_authenticate(self.admin)
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Document.objects.count(), 1)

    def test_duplicate_upload_rejected(self):
        self.client.force_authenticate(self.admin)
        self.upload()
        response = self.upload(name="copy.pdf")
        self.assertEqual(response.status_code, 400)

    def test_fake_pdf_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.upload(content=b"not a pdf", name="fake.pdf")
        self.assertEqual(response.status_code, 400)

    def test_learner_cannot_upload(self):
        self.client.force_authenticate(self.learner)
        response = self.upload()
        self.assertEqual(response.status_code, 403)