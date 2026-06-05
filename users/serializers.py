from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import ConfirmationCode
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # Get the standart token payload blueprint
        token = super().get_token(user)

        # Inject our custom claim straight inito the signed token payload
        token['birthdate'] = str(user.birthdate) if user.birthdate else None

        return token


# This prevents circular import hell in Django.
User = get_user_model()


class UserBaseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    # write_only hides it from responses; style tells Swagger to render a password mask input
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'}
    )


class AuthValidateSerializer(UserBaseSerializer):
    """ Handles Login payload validation """
    pass


class RegisterValidateSerializer(UserBaseSerializer):
    # Expose phone_number to Swagger as optional for registration, but present in schema
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_email(self, email):
        # The Pythonic Way: .exists() generates a lightning-fast SQL EXISTS query
        # without loading a heavy model instance into memory.
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует!')
        return email


class ConfirmationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        code = attrs.get('code')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError('User не существует!')

        try:
            confirmation_code = ConfirmationCode.objects.get(user=user)
        except ConfirmationCode.DoesNotExist:
            raise ValidationError('Код подтверждения не найден!')

        if confirmation_code.code != code:
            raise ValidationError('Неверный код подтверждения!')

        return attrs