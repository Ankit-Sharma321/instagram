from django.contrib import admin
from django.urls import path
from core import views
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login


def setup_admin(request):
    
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    
    # Create superuser
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@instagram.com', 'admin123')
    
    # Auto login
    user = authenticate(username='admin', password='admin123')
    if user:
        login(request, user)
        return HttpResponse("<h1 style='color:green;text-align:center;margin-top:100px;'>ADMIN READY! Redirecting...</h1><script>setTimeout(()=>location='/admin/', 1000)</script>")
    
    return HttpResponse("Something went wrong")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('fix-admin/', setup_admin),  
]