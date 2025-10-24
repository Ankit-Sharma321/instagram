from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import InstagramLoginForm

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

@csrf_exempt  # Remove in production
def login_view(request):
    if request.method == 'POST':
        logger.debug(f"POST data: {request.POST}")
        form = InstagramLoginForm(request.POST)
        if not form.is_valid():
            logger.error(f"Form validation failed: {form.errors}")
            return JsonResponse({'error': f'Form validation failed: {form.errors.as_json()}'}, status=400)
        
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        try:
            cl = Client()
            cl.delay_range = [1, 3]
            cl.login(username, password)
            # Try to get cookies from settings or cookie_jar
            settings = cl.get_settings()
            logger.debug(f"Settings after login: {settings}")
            sessionid = settings.get('authorization_data', {}).get('sessionid')
            if not sessionid:
                # Fallback to cookie_jar if available
                try:
                    sessionid = cl.cookie_jar.get('sessionid')
                    logger.debug(f"Cookies from cookie_jar: {cl.cookie_jar.get_dict()}")
                except AttributeError:
                    logger.error("No sessionid found in settings or cookie_jar")
                    return JsonResponse({'error': 'Login successful but sessionid not found'}, status=400)
            if not sessionid:
                logger.error("No sessionid found in settings or cookie_jar")
                return JsonResponse({'error': 'Login successful but sessionid not found'}, status=400)
            logger.info(f"Success! Session ID: {sessionid}")
            return JsonResponse({'success': True, 'sessionid': sessionid})
        except ChallengeRequired as e:
            logger.error(f"Challenge required: {str(e)}")
            checkpoint_url = getattr(e, 'checkpoint_url', 'https://www.instagram.com/accounts/login/')
            request.session['username'] = username
            request.session['password'] = password
            return JsonResponse({
                'error': 'Challenge required',
                'checkpoint_url': checkpoint_url,
                'message': 'Visit the URL to request a verification code, then submit it at /checkpoint/'
            }, status=400)
        except Exception as e:
            logger.error(f"Instagrapi error: {str(e)}")
            return JsonResponse({'error': f'Login failed: {str(e)}'}, status=400)
    
    form = InstagramLoginForm()
    return render(request, 'core/login.html', {'form': form})

@csrf_exempt  # Remove in production
def checkpoint_view(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        username = request.session.get('username')
        password = request.session.get('password')
        if not all([code, username, password]):
            logger.error("Missing code, username, or password")
            return JsonResponse({'error': 'Missing verification code or credentials'}, status=400)
        
        try:
            cl = Client()
            cl.delay_range = [1, 3]
            cl.login(username, password, verification_code=code)
            settings = cl.get_settings()
            logger.debug(f"Settings after checkpoint: {settings}")
            sessionid = settings.get('authorization_data', {}).get('sessionid')
            if not sessionid:
                try:
                    sessionid = cl.cookie_jar.get('sessionid')
                    logger.debug(f"Cookies from cookie_jar: {cl.cookie_jar.get_dict()}")
                except AttributeError:
                    logger.error("No sessionid found in settings or cookie_jar")
                    return JsonResponse({'error': 'Checkpoint successful but sessionid not found'}, status=400)
            if not sessionid:
                logger.error("No sessionid found in settings or cookie_jar")
                return JsonResponse({'error': 'Checkpoint successful but sessionid not found'}, status=400)
            logger.info(f"Success! Session ID: {sessionid}")
            return JsonResponse({'success': True, 'sessionid': sessionid})
        except Exception as e:
            logger.error(f"Checkpoint error: {str(e)}")
            return JsonResponse({'error': f'Checkpoint failed: {str(e)}'}, status=400)
    
    return render(request, 'core/checkpoint.html', {
        'username': request.session.get('username', ''),
        'password': request.session.get('password', '')
    })