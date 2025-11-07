from core import views
from django.urls import path
from django.contrib import admin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view),
    path('all-victims/', views.get_all_sessions), 
]