from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-json/', views.download_json),
]