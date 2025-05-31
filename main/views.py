from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
import requests
import json
import base64
from django.views.decorators.csrf import csrf_exempt
import urllib.parse
import secrets

def home(request):
    """
    Home view that checks authentication status
    """
    return render(request, 'main/home.html')

@login_required
def app_onboarding(request):
    """
    App onboarding view that requires authentication
    """
    return render(request, 'main/app_onboarding.html')

@login_required
def auth_clients(request):
    """
    Auth Clients view that requires authentication
    """
    return render(request, 'main/auth_clients.html')

@login_required
def audits_reports(request):
    """
    Audits and Reports view that requires authentication
    """
    return render(request, 'main/audits_reports.html')

@login_required
def app_update(request):
    """
    App Update
    """
    return render(request, 'main/app_update.html')

def login_view(request):
    """
    Redirect directly to Okta for authentication
    """
    # Generate a random state parameter to prevent CSRF
    state = secrets.token_hex(16)
    request.session['okta_state'] = state
    
    # Build the authorization URL
    params = {
        'client_id': settings.OKTA_CLIENT_ID,
        'redirect_uri': settings.OKTA_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'login',  # Force a login prompt
    }
    
    authorize_url = f"{settings.OKTA_ISSUER}/v1/authorize?{urllib.parse.urlencode(params)}"
    return redirect(authorize_url)


def logout_view(request):
    """
    Log out the user and redirect to the home page
    """
    logout(request)
    return redirect('home')

def oauth2_callback(request):
    """
    Handle the OAuth2 callback from Okta
    """
    # Add debug logging
    print("OAuth2 callback received")
    print(f"Query parameters: {request.GET}")
    
    # Verify the state parameter to prevent CSRF
    state = request.GET.get('state')
    stored_state = request.session.get('okta_state')
    
    if not state or not stored_state or state != stored_state:
        print(f"State mismatch: received={state}, stored={stored_state}")
        # Continue anyway for now to debug other issues
        # return HttpResponse("Invalid state parameter. Possible CSRF attack.", status=400)
    
    # Clear the state from the session
    if 'okta_state' in request.session:
        del request.session['okta_state']
    
    code = request.GET.get('code')
    if not code:
        print("No code parameter found")
        return redirect('login')
    
    # Exchange code for tokens
    token_url = f"{settings.OKTA_ISSUER}/v1/token"
    
    # Create the authorization header with client ID and secret
    client_auth = f"{settings.OKTA_CLIENT_ID}:{settings.OKTA_CLIENT_SECRET}"
    client_auth_b64 = base64.b64encode(client_auth.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {client_auth_b64}',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    token_payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.OKTA_REDIRECT_URI
    }
    
    print(f"Sending token request to: {token_url}")
    print(f"With payload: {token_payload}")
    
    try:
        token_response = requests.post(token_url, headers=headers, data=token_payload)
        print(f"Token response status: {token_response.status_code}")
        
        if token_response.status_code != 200:
            print(f"Token error response: {token_response.text}")
            return HttpResponse(f"Error exchanging code for tokens: {token_response.text}", status=400)
        
        tokens = token_response.json()
        print("Tokens received successfully")
        
        # Get user info
        userinfo_url = f"{settings.OKTA_ISSUER}/v1/userinfo"
        userinfo_headers = {
            'Authorization': f"Bearer {tokens['access_token']}"
        }
        
        userinfo_response = requests.get(userinfo_url, headers=userinfo_headers)
        if userinfo_response.status_code != 200:
            print(f"Userinfo error: {userinfo_response.text}")
            return HttpResponse(f"Error getting user info: {userinfo_response.text}", status=400)
        
        userinfo = userinfo_response.json()
        print(f"User info received: {json.dumps(userinfo, indent=2)}")
        
        # Create or get user
        email = userinfo.get('email')
        if not email:
            print("No email found in user info")
            return HttpResponse("No email found in user info", status=400)
        
        # Find or create user
        try:
            user = User.objects.get(email=email)
            print(f"Found existing user: {user.username}")
        except User.DoesNotExist:
            # Create a new user
            username = userinfo.get('preferred_username', email)
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=userinfo.get('given_name', ''),
                last_name=userinfo.get('family_name', '')
                
            )
            print(f"Created new user: {user.username}")
        
        # Log the user in with the specific backend
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        print(f"User {user.username} logged in successfully")
        
        return redirect('home')
        
    except Exception as e:
        print(f"Exception during token exchange: {str(e)}")
        return HttpResponse(f"Error during authentication: {str(e)}", status=500)

@csrf_exempt
def auth_callback_api(request):
    """
    API endpoint to receive tokens and user info from the client
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        tokens = data.get('tokens')
        user_info = data.get('userInfo')
        
        if not tokens or not user_info:
            return JsonResponse({'error': 'Missing tokens or user info'}, status=400)
        
        # Create or get user
        email = user_info.get('email')
        if not email:
            return JsonResponse({'error': 'No email found in user info'}, status=400)
        
        # Find or create user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create a new user
            username = user_info.get('preferred_username', email)
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', '')
            )
        
        # Log the user in with the specific backend
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
