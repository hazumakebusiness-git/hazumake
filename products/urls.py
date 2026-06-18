# products/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop, name='shop'),                          # /shop/ — all games
    path('<slug:slug>/verify-player/', views.verify_player_view, name='verify_player'),
    path('product/<uuid:pk>/', views.product_detail, name='product_detail'),
    path('<slug:game_slug>/', views.game_shop, name='game_shop'),  # /shop/mobile-legends/
]

