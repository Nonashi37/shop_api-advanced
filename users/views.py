import random
import string
from django.db import transaction
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer
)
from .models import ConfirmationCode

# Look up the custom user model dynamically
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


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

            # Record login timestamp
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

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

        validated_data = serializer.validated_data
        email = validated_data.get('email')
        password = validated_data.get('password')
        phone_number = validated_data.get('phone_number')
        birthdate = validated_data.get('birthdate')
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')

        # Use transaction to ensure data consistency
        with transaction.atomic():
            # Create user explicitly using the manager method
            user = User.objects.create_user(
                email=email,
                password=password,
                phone_number=phone_number,
                birthdate=birthdate,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # Must be activated via OTP code
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
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_444_NOT_FOUND,
                    data={'error': 'User not found!'}
                )

            user.is_active = True
            user.last_login = timezone.now()
            user.save(update_fields=['is_active', 'last_login'])

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