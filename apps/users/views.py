# Python modules
import logging
from typing import Any

# Django modules
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

# DRF modules
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.viewsets import ViewSet

# SimpleJWT modules
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

# drf-spectacular modules
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

# Third-party modules
from django_ratelimit.decorators import ratelimit

# Project modules
from apps.users.models import CustomUser
from apps.users.serializers import (
    AccessTokenResponseSerializer,
    CustomUserSerializer,
    ErrorResponseSerializer,
    LoginSerializer,
    MessageResponseSerializer,
    RegisterSerializer,
    TokenPairResponseSerializer,
)
from .permissions import IsOwnerOrAdmin


logger = logging.getLogger(__name__)


class AuthViewSet(ViewSet):
    """
    Users can register, login, refresh tokens, logout, and manage their profile.

    - POST /users/register/       - Register a new user
    - POST /users/login/          - Login and receive JWT tokens
    - POST /users/token/refresh/  - Refresh access token using refresh token
    - POST /users/logout/         - Logout and blacklist refresh token
    - GET  /users/me/             - Retrieve own profile
    - PATCH /users/me/update/     - Update own profile
    - GET  /users/                - List all users (admin only)
    """

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action in {"register", "login", "refresh"}:
            return [AllowAny()]
        if self.action in {"me", "me_update"}:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Login (get JWT tokens)",
        description="Authenticate user and return JWT access and refresh tokens.",
        request=LoginSerializer,
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Successful login",
                response=TokenPairResponseSerializer,
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid credentials",
                response=ErrorResponseSerializer,
            ),
        },
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Login success",
                value={
                    "access": "access_token",
                    "refresh": "refresh_token",
                },
                response_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="login")
    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def login(self, request: Request) -> Response:
        """Authenticate user and return JWT tokens."""
        logger.info(f"Login attempt with email: {request.data.get('email')}")

        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            logger.info(f"User logged in successfully with email: {user.email}")
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=HTTP_200_OK,
            )

        logger.warning(f"Login failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Register",
        description="Register a new user with email, password, first name, and last name.",
        request=RegisterSerializer,
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Successful registration",
                response=CustomUserSerializer,
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation errors",
                response=ErrorResponseSerializer,
            ),
        },
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Registration success",
                value={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                    "password": "password123",
                    "password2": "password123",
                },
                response_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="register")
    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def register(self, request: Request) -> Response:
        """Register a new user."""
        logger.info(f"Registration attempt with email: {request.data.get('email')}")

        serializer = RegisterSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User registered successfully with email: {user.email}")
            return Response(
                {
                    "message": _("User registered successfully"),
                    "user": CustomUserSerializer(user).data,
                },
                status=HTTP_200_OK,
            )

        logger.warning(f"Registration failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Refresh access token",
        description="Refresh JWT access token using a valid refresh token.",
        request=TokenRefreshSerializer,
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Token refresh successful",
                response=AccessTokenResponseSerializer,
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Invalid or expired refresh token",
                response=ErrorResponseSerializer,
            ),
        },
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Refresh request",
                value={"refresh": "refresh_token"},
                request_only=True,
            ),
            OpenApiExample(
                "Refresh success",
                value={"access": "new_access_token"},
                response_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="token/refresh")
    def refresh(self, request: Request) -> Response:
        """Refresh access token using refresh token."""
        logger.info("Token refresh attempt")

        serializer = TokenRefreshSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken) as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise InvalidToken(e)

        logger.info("Token refresh successful")
        return Response(serializer.validated_data, status=HTTP_200_OK)

    @extend_schema(
        summary="Logout",
        description="Logout and blacklist the refresh token.",
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Logout successful",
                response=MessageResponseSerializer,
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid token",
                response=ErrorResponseSerializer,
            ),
        },
        tags=["Auth"],
    )
    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request: Request) -> Response:
        """Logout and blacklist refresh token."""
        logger.info(f"Logout attempt for email: {request.user.email}")

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"Logout successful for email: {request.user.email}")
            return Response({"message": _("Logout successful")}, status=HTTP_200_OK)
        except Exception as e:
            logger.warning(
                f"Logout failed with error: {str(e)} for email: {request.user.email}"
            )
            return Response({"error": _("Invalid token")}, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get my profile",
        description="Retrieve the authenticated user's profile information.",
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Profile retrieved successfully",
                response=CustomUserSerializer,
            ),
        },
        tags=["Users"],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated, IsOwnerOrAdmin],
    )
    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def me(self, request: Request) -> Response:
        """Retrieve own profile."""
        user = request.user
        self.check_object_permissions(request, user)
        return Response(CustomUserSerializer(user).data, status=HTTP_200_OK)

    @extend_schema(
        summary="Update my profile",
        description="Update the authenticated user's profile information.",
        request=CustomUserSerializer,
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Profile updated successfully",
                response=CustomUserSerializer,
            ),
        },
        tags=["Users"],
        examples=[
            OpenApiExample(
                "Patch example",
                value={
                    "first_name": "John",
                    "last_name": "Doe",
                },
                request_only=True,
            ),
        ],
    )
    @action(
        detail=False,
        methods=["patch"],
        url_path="me/update",
        permission_classes=[IsAuthenticated, IsOwnerOrAdmin],
    )
    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def me_update(self, request: Request) -> Response:
        """Update own profile."""
        user = request.user
        self.check_object_permissions(request, user)

        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(CustomUserSerializer(serializer.instance).data, status=HTTP_200_OK)

    @extend_schema(
        summary="List users (admin only)",
        description="List all users in the system. Admin access required.",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search users by email, first name, or last name",
                required=False,
                type=str,
            ),
        ],
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="List of users retrieved successfully",
                response=CustomUserSerializer(many=True),
            ),
        },
        tags=["Users"],
    )
    def list(self, request: Request) -> Response:
        """List all users with optional search filter."""
        search = request.query_params.get("search")
        queryset = CustomUser.objects.all().order_by("id")

        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        logger.info(
            f"User list requested by id {request.user.id} with email {request.user.email}"
        )
        return Response(
            CustomUserSerializer(queryset, many=True).data,
            status=HTTP_200_OK,
        )