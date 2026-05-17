from django.urls import path, include
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('google-login/', RedirectView.as_view(url='/accounts/google/login/', permanent=False), name='google_login'),
    path('', include('allauth.urls')),
]