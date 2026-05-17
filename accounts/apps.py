from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals

        try:
            from django.conf import settings
            from django.db.models.signals import post_migrate
            from django.dispatch import receiver
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp
        except ImportError:
            return

        @receiver(post_migrate)
        def ensure_google_social_app(sender, **kwargs):
            if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
                return
            if not Site.objects.filter(id=settings.SITE_ID).exists():
                return
            site = Site.objects.get(id=settings.SITE_ID)
            social_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'secret': settings.GOOGLE_CLIENT_SECRET,
                }
            )
            if created or site not in social_app.sites.all():
                social_app.sites.add(site)
                social_app.client_id = settings.GOOGLE_CLIENT_ID
                social_app.secret = settings.GOOGLE_CLIENT_SECRET
                social_app.save()
