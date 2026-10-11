import io
import unittest
from unittest.mock import patch

from fastapi import HTTPException, UploadFile

from app.routes.documents import validate_pdf_upload


class TestPdfUploadValidation(unittest.TestCase):
    def make_upload(self, content, filename="document.pdf"):
        return UploadFile(filename=filename, file=io.BytesIO(content))

    def test_accepts_pdf_signature_and_rewinds_stream(self):
        upload = self.make_upload(b"%PDF-1.7 sample")

        validate_pdf_upload(upload)

        self.assertEqual(upload.file.tell(), 0)

    def test_accepts_pdf_header_within_initial_1024_bytes(self):
        upload = self.make_upload(b" " * 20 + b"%PDF-1.7 sample")

        validate_pdf_upload(upload)

        self.assertEqual(upload.file.tell(), 0)

    def test_rejects_non_pdf_filename(self):
        upload = self.make_upload(b"%PDF-1.7 sample", filename="document.txt")

        with self.assertRaises(HTTPException) as error:
            validate_pdf_upload(upload)

        self.assertEqual(error.exception.status_code, 400)

    def test_rejects_invalid_pdf_signature(self):
        upload = self.make_upload(b"plain text file")

        with self.assertRaises(HTTPException) as error:
            validate_pdf_upload(upload)

        self.assertEqual(error.exception.status_code, 400)

    def test_rejects_empty_pdf(self):
        upload = self.make_upload(b"")

        with self.assertRaises(HTTPException) as error:
            validate_pdf_upload(upload)

        self.assertEqual(error.exception.status_code, 400)

    def test_rejects_upload_over_configured_size_limit(self):
        upload = self.make_upload(b"%PDF-123456")

        with (
            patch(
                "app.routes.documents.settings.MAX_UPLOAD_SIZE_BYTES",
                10,
            ),
            self.assertRaises(HTTPException) as error,
        ):
            validate_pdf_upload(upload)

        self.assertEqual(error.exception.status_code, 413)
        self.assertIn("maximum upload size", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
