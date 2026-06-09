import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def exchange_code_for_google_user(code: str, redirect_uri: str) -> dict:
    """
    Executes the manual OAuth 2.0 authorization code exchange with Google APIs.
    """
    # Phase 1: Trade Authorization Code for an Access Token
    token_payload = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    
    token_response = requests.post(GOOGLE_TOKEN_URL, data=token_payload)
    if not token_response.ok:
        raise AuthenticationFailed("Failed to exchange code for access token with Google.")
        
    access_token = token_response.json().get('access_token')

    # Phase 2: Use Access Token to fetch the user's profile info
    headers = {'Authorization': f'Bearer {access_token}'}
    userinfo_response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
    
    if not userinfo_response.ok:
        raise AuthenticationFailed("Failed to fetch user profile information from Google.")
        
    return userinfo_response.json()