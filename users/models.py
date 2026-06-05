from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone
from users.managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Regex validator for standart international phone formants (like: +123456780)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    email = models.EmailField(unique=True, max_length=255) # at any rate
    # Blank and null are True so regular users aren't forced to procide it on registration
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    # Any field here is automaticall required by 'createsuperuser'
    REQUIRED_FIELDS = ['phone_number']
    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email or ""


class ConfirmationCode(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='confirmation_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Код подтверждения для {self.user.username}"
