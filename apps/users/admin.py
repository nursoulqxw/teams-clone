from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from apps.users.models import CustomUser
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser 
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
        "last_login",

    )
    list_filter = (
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",

    )

    search_fields = (
        "email",
        "first_name",
        "last_name",

    )
    ordering = ("-date_joined",)

    readonly_fields = (
        "date_joined",
        "last_login",
    )    
    fieldsets = (
        (None, {
            "fields": (
                "email",
                "password",
            )
        }),
        ("Personal Info", {
            "fields": (
                "first_name",
                "last_name",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
        ("Important dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "first_name",
                "last_name",
                "password1",
                "password2",
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
    )