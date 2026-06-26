"""accounts/urls.py — 用户路由"""
from django.urls import path

from accounts import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('u/<str:username>/', views.profile_view, name='profile'),
    path('u/<str:username>/favorites/', views.favorites_view, name='favorites'),
    path('u/<str:username>/followers/', views.followers_view, name='followers'),
    path('u/<str:username>/following/', views.following_view, name='following'),
    # 私信
    path('messages/', views.messages_inbox, name='messages_inbox'),
    path('messages/<str:username>/', views.messages_conversation, name='messages_conversation'),
    path('messages/<str:username>/send/', views.messages_send, name='messages_send'),
]
