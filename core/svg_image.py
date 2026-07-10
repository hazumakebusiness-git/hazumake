import os
import re
import xml.etree.ElementTree as ET

from django import forms
from django.contrib.admin.widgets import AdminFileWidget
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import ImageField
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
SVG_EXTENSION = 'svg'
ALLOWED_IMAGE_EXTENSIONS = IMAGE_EXTENSIONS + [SVG_EXTENSION]
MAX_SVG_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
SVG_DANGEROUS_PATTERN = re.compile(
    r'(<\s*script\b|<\s*foreignObject\b|on\w+\s*=|javascript:|xlink:href\s*=)',
    re.IGNORECASE,
)


def _get_extension(filename):
    return os.path.splitext(filename)[1].lstrip('.').lower()


def is_svg_filename(filename):
    return _get_extension(filename) == SVG_EXTENSION


def validate_svg_file(uploaded_file):
    if uploaded_file.size > MAX_SVG_FILE_SIZE:
        raise ValidationError(
            _('SVG file size must be under %(max_size)s MB.'),
            params={'max_size': MAX_SVG_FILE_SIZE // (1024 * 1024)},
        )

    try:
        content_bytes = uploaded_file.read()
    finally:
        uploaded_file.seek(0)

    try:
        text = content_bytes.decode('utf-8', errors='replace')
    except (AttributeError, TypeError):
        raise ValidationError(_('Uploaded SVG file could not be decoded.'))

    if SVG_DANGEROUS_PATTERN.search(text):
        raise ValidationError(_('SVG file contains unsupported or unsafe markup.'))

    if re.search(r'<\s*svg\b', text, re.IGNORECASE) is None:
        raise ValidationError(_('Uploaded file does not appear to be a valid SVG.'))

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        raise ValidationError(_('Uploaded SVG file is not well-formed XML.'))

    if not root.tag.lower().endswith('svg'):
        raise ValidationError(_('Uploaded file is not a valid SVG document.'))


class SVGImageFormField(forms.FileField):
    default_validators = [FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS)]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', SVGAdminFileWidget())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if data in self.empty_values:
            return None

        if is_svg_filename(getattr(data, 'name', '')):
            uploaded_file = super().clean(data, initial)
            validate_svg_file(uploaded_file)
            return uploaded_file

        return forms.ImageField().clean(data, initial)


class SVGAdminFileWidget(AdminFileWidget):
    def __init__(self, attrs=None):
        default_attrs = {'accept': 'image/*,image/svg+xml'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)

        if value and getattr(value, 'url', None):
            preview_html = format_html(
                '<div style="margin-top: .5rem; max-width: 320px;">'
                '<img src="{}" alt="{} preview" style="max-height: 180px; max-width: 100%; border: 1px solid #ddd;" />'
                '</div>',
                value.url,
                name,
            )
            return mark_safe(output + preview_html)

        return output


class SVGImageAdminMixin:
    formfield_overrides = {
        ImageField: {
            'form_class': SVGImageFormField,
            'widget': SVGAdminFileWidget,
        }
    }
