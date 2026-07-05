from django import template
from django.conf import settings
from ..models import SiteSettings, PageBackground

register = template.Library()

@register.simple_tag
def get_site_settings():
    return SiteSettings.get()


@register.simple_tag(takes_context=True)
def page_background_style(context):
    request = context.get('request')
    if not request:
        return ''

    page_identifier = getattr(request, 'page_identifier', None)
    if not page_identifier:
        page_identifier = request.resolver_match.view_name if getattr(request, 'resolver_match', None) else None

    if not page_identifier:
        return ''

    background = PageBackground.objects.filter(page_identifier=page_identifier).first()
    if not background:
        return ''

    if background.background_type == 'image' and background.background_image:
        return f"background-image: url('{background.background_image.url}'); background-size: cover; background-position: center; background-repeat: no-repeat;"

    if background.background_type == 'color' and background.background_color:
        return f"background-color: {background.background_color};"

    return ''