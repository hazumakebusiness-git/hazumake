from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from products.views import home

urlpatterns = [
    path('hazumake-control/', admin.site.urls),
    path('', include('auth.urls')),
    path('', home, name='home'),
    path('', include('core.urls')),
    path('shop/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('wallet/', include('wallet.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include('payments.urls', namespace='payments')),
    path('api/', include('api.urls')),
    # Redirect old login/register to new Firebase auth pages
    path('login/', RedirectView.as_view(url='/accounts/login/'), name='login_redirect'),
    path('register/', RedirectView.as_view(url='/accounts/register/'), name='register_redirect'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])