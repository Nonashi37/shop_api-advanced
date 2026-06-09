import random
import string
from django.db import transaction
from django.contrib.auth import authenticate, get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status, serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .oauth import exchange_code_for_google_user

from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer
)
from .models import ConfirmationCode

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Look up the custom user model dynamically
User = get_user_model()

class GoogleLoginSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, help_text="The authorization code returned from Google.")
    redirect_uri = serializers.CharField(required=True, help_text="Must perfectly match the redirect URI sent to Google.")

class GoogleLoginAPIView(APIView):
    """
    Handles incoming Google OAuth codes, provisions users, and issues application JWTs.
    """
    # Public route, no auth headers needed to hit this!
    permission_classes = [] 

    def post(self, request, *args, **kwargs):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        redirect_uri = serializer.validated_data['redirect_uri']
        
        # Run the HTTP handshake
        google_profile = exchange_code_for_google_user(code=code, redirect_uri=redirect_uri)
        
        email = google_profile.get('email')
        given_name = google_profile.get('given_name', '')
        family_name = google_profile.get('family_name', '')
        
        if not email:
            return Response({"error": "Google profile did not supply an email address."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Database Provisioning Phase (Get or Create)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': given_name,
                'last_name': family_name,
                'registration_source': 'google',
                'is_active': True, # Rule 1: Make user active explicitly on signup
            }
        )
        
        # Ensure rules apply to existing users returning via Google
        if not user.is_active:
            user.is_active = True
            
        # Rule 2: Save the date and time of the last login
        user.last_login = timezone.now()
        user.save()
        
        # Generate standard SimpleJWT tokens for our app architecture
        refresh = RefreshToken.for_user(user)
        
        # Custom claim injection manually since we are outside the standard TokenObtainPairView
        refresh['birthdate'] = str(user.birthdate) if user.birthdate else None
        
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "registration_source": user.registration_source
            }
        }, status=status.HTTP_200_OK)


class AuthorizationAPIView(GenericAPIView):
    serializer_class = AuthValidateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Django's authenticate() specifically looks for the 'username' keyword argument,
        # even when your USERNAME_FIELD is rewritten to use email.
        user = authenticate(
            username=serializer.validated_data.get('email'),
            password=serializer.validated_data.get('password')
        )

        if user:
            if not user.is_active:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={'error': 'User account is not activated yet!'}
                )

            token, _ = Token.objects.get_or_create(user=user)
            return Response(data={'key': token.key})

        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={'error': 'User credentials are wrong!'}
        )


class RegistrationAPIView(GenericAPIView):
    serializer_class = RegisterValidateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use transaction to ensure data consistency
        with transaction.atomic():
            # Unpack validated_data so phone_number, email, 
            # and password are all passed and saved automatically!
            user = User.objects.create_user(
                **serializer.validated_data,
                is_active=False
            )

            # Create a random 6-digit verification code
            code = ''.join(random.choices(string.digits, k=6))
            ConfirmationCode.objects.create(user=user, code=code)

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'user_id': user.id,
                'confirmation_code': code
            }
        )


class ConfirmUserAPIView(GenericAPIView):
    serializer_class = ConfirmationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']

        with transaction.atomic():
            # Fetch user safely using the dynamic User reference
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()

            token, _ = Token.objects.get_or_create(user=user)
            
            # Clear out the used confirmation token
            ConfirmationCode.objects.filter(user=user).delete()

        return Response(
            status=status.HTTP_200_OK,
            data={
                'message': 'User аккаунт успешно активирован',
                'key': token.key
            }
        )