from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("role", "designation", "department")}),
    )
    list_display = ("username", "email", "role", "department", "is_staff")
    list_filter = ("role", "department")