import random
import string
from django.db import transaction
from django.contrib.auth import authenticate, get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer
)
from .models import ConfirmationCode

# Look up the custom user model dynamically
User = get_user_model()


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