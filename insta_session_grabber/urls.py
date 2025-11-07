from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    # path('checkpoint/', views.checkpoint_view, name='checkpoint'),
]


from django.contrib.auth.models import User
from django.http import HttpResponse

def create_superuser_view(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@instagram.com', 'admin123')
        return HttpResponse("<h1 style='color:green; text-align:center; margin-top:100px;'>ADMIN CREATED SUCCESSFULLY!<br><br>Username: admin<br>Password: admin123<br><br><a href='/admin' style='color:#0095f6; font-size:20px;'>Click here to go to Admin Panel</a></h1>")
    return HttpResponse("<h1>Admin already exists! Go to <a href='/admin'>/admin</a></h1>")

urlpatterns += [path('create-admin/', create_superuser_view)]