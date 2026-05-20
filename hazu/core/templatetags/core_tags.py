from django import template
from ..models import SiteSettings

register = template.Library()

@register.simple_tag
def get_site_settings():
    return SiteSettings.get()