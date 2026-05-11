from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.users.models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin model for CustomUser.
    Inherits from UserAdmin to ensure proper password hashing and permissions management.
    """
    model = CustomUser
    
    # Fields shown in the user list view
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
    
    # Sidebar filters
    list_filter = (
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
    )
    
    # Fields searchable in the admin interface
    search_fields = (
        "email", 
        "first_name", 
        "last_name"
    )
    
    ordering = ("-date_joined",)
    
    readonly_fields = (
        "date_joined",
        "last_login",
    )

    # Layout for the 'Change User' form
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Layout for the 'Add User' form
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
            ),
        }),
    )