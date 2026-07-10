from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase

from .svg_image import SVGImageFormField


class SVGImageValidationTests(TestCase):
    def test_valid_svg_upload(self):
        svg_content = b'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'
        uploaded = SimpleUploadedFile('test.svg', svg_content, content_type='image/svg+xml')
        field = SVGImageFormField()
        cleaned = field.clean(uploaded)
        self.assertEqual(cleaned.name, 'test.svg')

    def test_malicious_svg_is_rejected(self):
        svg_content = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><script>alert("x")</script></svg>'
        uploaded = SimpleUploadedFile('bad.svg', svg_content, content_type='image/svg+xml')
        field = SVGImageFormField()
        with self.assertRaises(ValidationError):
            field.clean(uploaded)

    def test_png_upload_still_valid(self):
        png_content = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
            b'\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01E\x86\x8d\x1b'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        uploaded = SimpleUploadedFile('test.png', png_content, content_type='image/png')
        field = SVGImageFormField()
        cleaned = field.clean(uploaded)
        self.assertEqual(cleaned.name, 'test.png')

    def test_invalid_extension_is_rejected(self):
        content = b'not an image'
        uploaded = SimpleUploadedFile('test.txt', content, content_type='text/plain')
        field = SVGImageFormField()
        with self.assertRaises(ValidationError):
            field.clean(uploaded)
