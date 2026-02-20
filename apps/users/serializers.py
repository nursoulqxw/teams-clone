import logging 
from typing import Any


from rest_framework.serializers import (
    EmailField,
    CharField,
    BooleanField,
    SerializerMethodField,
    Serializer,
    ValidationError,
    ModelSerializer,
    
)
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import CustomUser
from rest_framework import serializers

logger = logging.getLogger(__name__)


class CustomUserSerializer(ModelSerializer):
    
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
    
    def to_representation(self, instance):
        logger.debug(f"Serializing user with email: {instance.email}")

        return super().to_representation(instance)
    
    
class RegisterSerializer(ModelSerializer):
    password = CharField(
        write_only=True,
        min_length=8,
    )
    password2 = CharField (
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
        email = attrs.get("email", "")
        logger.debug(f"Validating registration for email: {email}")

        if attrs["password"] != attrs["password2"]:
            logger.warning(f"Password mismatch for email: {email}")
            raise ValidationError("Passwords do not match")
        logger.debug(f"Registration data validated for email: {email}")
        return attrs
    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        email = validated_data.get("email", "")
        logger.debug(f"Creating user with email: {email}")
        validated_data.pop("password2", None)  # Remove password2 as it's not needed for user creation
        user = CustomUser.objects.create_user(**validated_data)
        logger.info(f"User created successfully with email: {email}, id: {user.id}")

        return user
    def get_token(self, obj: CustomUser) -> str:
        # Implement token generation logic here, e.g., using
        # JWT or any other token generation method
        refresh = RefreshToken.for_user(obj)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    


class LoginSerializer(Serializer):
    email = EmailField()
    password = CharField(write_only=True)
    access = CharField(read_only=True)
    refresh = CharField(read_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
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
        attrs["user"] = user  # ✅ ДОБАВЬ
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)
        return attrs
    
class UserListSerializer(ModelSerializer):
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
    refresh = CharField(write_only=True)

class TokenPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class AccessTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()