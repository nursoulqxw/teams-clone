# Python modules
import logging
from typing import Any

# Django modules
from django.contrib.auth import authenticate

# DRF modules
from rest_framework.serializers import (
    CharField,
    EmailField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)
from rest_framework_simplejwt.tokens import RefreshToken

# Project modules
from apps.users.models import CustomUser


logger = logging.getLogger(__name__)


class CustomUserSerializer(ModelSerializer):
    """Serializer for full CustomUser representation."""

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "is_superuser",
            "date_joined",
            "last_login",
        )
        read_only_fields = (
            "id",
            "date_joined",
            "last_login",
        )

    def to_representation(self, instance: CustomUser) -> dict[str, Any]:
        """Log and return serialized user data."""
        logger.debug(f"Serializing user with email: {instance.email}")
        return super().to_representation(instance)


class RegisterSerializer(ModelSerializer):
    """Serializer for user registration."""

    password = CharField(
        write_only=True,
        min_length=8,
    )
    password2 = CharField(
        write_only=True,
        min_length=8,
    )
    token = SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "token",
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that passwords match."""
        email = attrs.get("email", "")
        logger.debug(f"Validating registration for email: {email}")

        if attrs["password"] != attrs["password2"]:
            logger.warning(f"Password mismatch for email: {email}")
            raise ValidationError("Passwords do not match")

        logger.debug(f"Registration data validated for email: {email}")
        return attrs

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        """Create and return a new user."""
        email = validated_data.get("email", "")
        logger.debug(f"Creating user with email: {email}")

        validated_data.pop("password2", None)
        user = CustomUser.objects.create_user(**validated_data)

        logger.info(f"User created successfully with email: {email}, id: {user.id}")
        return user

    def get_token(self, obj: CustomUser) -> dict[str, str]:
        """Generate and return JWT token pair for the user."""
        refresh = RefreshToken.for_user(obj)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class LoginSerializer(Serializer):
    """Serializer for user login."""

    email = EmailField()
    password = CharField(write_only=True)
    access = CharField(read_only=True)
    refresh = CharField(read_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate credentials and attach tokens to attrs."""
        email = attrs.get("email", "")
        password = attrs.get("password", "")
        logger.debug(f"Validating login for email: {email}")

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if not user or not user.is_active:
            logger.warning(f"Login failed for email: {email}")
            raise ValidationError("Invalid credentials or inactive account")

        logger.info(f"Login successful for email: {email}")
        refresh = RefreshToken.for_user(user)
        logger.debug(f"Generated tokens for email: {email}")

        attrs["user"] = user
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)
        return attrs


class UserListSerializer(ModelSerializer):
    """Serializer for listing users."""

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "is_superuser",
        )


class LogoutSerializer(Serializer):
    """Serializer for user logout."""

    refresh = CharField(write_only=True)


class TokenPairResponseSerializer(Serializer):
    """Serializer for JWT token pair response."""

    access = CharField()
    refresh = CharField()


class MessageResponseSerializer(Serializer):
    """Serializer for message response."""

    message = CharField()


class ErrorResponseSerializer(Serializer):
    """Serializer for error response."""

    error = CharField()


class AccessTokenResponseSerializer(Serializer):
    """Serializer for access token response."""

    access = CharField()
