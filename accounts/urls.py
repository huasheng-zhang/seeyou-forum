"""accounts/urls.py — 用户路由"""
from django.urls import path

from accounts import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('u/<str:username>/', views.profile_view, name='profile'),
    path('u/<str:username>/favorites/', views.favorites_view, name='favorites'),
]
