"""
URL configuration for hazu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    # Custom accounts URLs MUST come before django.contrib.auth.urls
    # so our password reset views take precedence over Django's default ones
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/auth/', include('allauth.urls')),  # Google OAuth at /accounts/auth/google/login/
    path('accounts/google-login/', RedirectView.as_view(url='/accounts/auth/google/login/', permanent=False), name='google_login'),
    path('api/', include('payments.urls', namespace='payments')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])