"""boards/urls.py — 论坛路由"""
from django.urls import path

from boards import views

urlpatterns = [
    path('', views.home, name='home'),
    path('board/<slug:slug>/', views.board_detail, name='board_detail'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.post_create, name='post_create'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('search/', views.search, name='search'),
    # AJAX APIs
    path('api/post/<int:pk>/like/', views.toggle_like, name='api_like'),
    path('api/post/<int:pk>/favorite/', views.toggle_favorite, name='api_favorite'),
    path('api/post/<int:pk>/comment/', views.post_comment, name='api_comment'),
    path('api/user/<str:username>/follow/', views.toggle_follow, name='api_follow'),
]
