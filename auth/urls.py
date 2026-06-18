from django.urls import path
from . import views

urlpatterns = [
    path('auth/signup/', views.signup_view, name='signup'),
    path('auth/signin/', views.signin_view, name='signin'),
    path('auth/signout/', views.signout_view, name='signout'),
    path('auth/firebase-session/', views.firebase_session, name='firebase_session'),
]
