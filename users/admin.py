from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Control what fields show up in the user list view
    list_display = ['email', 'phone_number', 'is_staff', 'is_active']
    
    # Control what fields show up when editing a user
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('phone_number',)}),
    )
    # Control fields when creating a user
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('phone_number',)}),
    )
    ordering = ['email']

admin.site.register(CustomUser, CustomUserAdmin)