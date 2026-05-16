# Python modules
import logging

# Django modules
from django.urls import reverse

# DRF modules
from rest_framework.test import APITestCase
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)

# SimpleJWT modules
from rest_framework_simplejwt.tokens import RefreshToken

# Project modules
from apps.users.models import CustomUser


logger = logging.getLogger(__name__)


class RegisterTestCase(APITestCase):
    """Tests for POST /api/users/register/"""

    def setUp(self) -> None:
        self.url = reverse("users-register")
        self.valid_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "strongpass123",
            "password2": "strongpass123",
        }

    def test_register_success(self) -> None:
        """Good case: valid data → 200"""
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn("user", response.data)

    def test_register_duplicate_email(self) -> None:
        """Bad case 1: duplicate email → 400"""
        CustomUser.objects.create_user(
            email="test@example.com",
            password="strongpass123",
            first_name="Test",
            last_name="User",
        )
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_empty_fields(self) -> None:
        """Bad case 2: empty fields → 400"""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class LoginTestCase(APITestCase):
    """Tests for POST /api/users/login/"""

    def setUp(self) -> None:
        self.url = reverse("users-login")
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="strongpass123",
            first_name="Test",
            last_name="User",
        )

    def test_login_success(self) -> None:
        """Good case: valid credentials → 200"""
        response = self.client.post(
            self.url,
            {"email": "test@example.com", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self) -> None:
        """Bad case 1: wrong password → 400"""
        response = self.client.post(
            self.url,
            {"email": "test@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_email(self) -> None:
        """Bad case 2: nonexistent email → 400"""
        response = self.client.post(
            self.url,
            {"email": "nouser@example.com", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class RefreshTestCase(APITestCase):
    """Tests for POST /api/users/token/refresh/"""

    def setUp(self) -> None:
        self.url = reverse("users-refresh")
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="strongpass123",
            first_name="Test",
            last_name="User",
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_refresh_success(self) -> None:
        """Good case: valid refresh token → 200"""
        response = self.client.post(
            self.url,
            {"refresh": str(self.refresh)},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_invalid_token(self) -> None:
        """Bad case 1: invalid token → 401"""
        response = self.client.post(
            self.url,
            {"refresh": "invalidtoken"},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_refresh_empty_token(self) -> None:
        """Bad case 2: empty token → 400"""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class LogoutTestCase(APITestCase):
    """Tests for POST /api/users/logout/"""

    def setUp(self) -> None:
        self.url = reverse("users-logout")
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="strongpass123",
            first_name="Test",
            last_name="User",
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(self.refresh.access_token)}"
        )

    def test_logout_success(self) -> None:
        """Good case: valid refresh token → 200"""
        response = self.client.post(
            self.url,
            {"refresh": str(self.refresh)},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_logout_without_token(self) -> None:
        """Bad case 1: no refresh token → 400"""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_logout_invalid_token(self) -> None:
        """Bad case 2: invalid refresh token → 400"""
        response = self.client.post(
            self.url,
            {"refresh": "invalidtoken"},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class MeTestCase(APITestCase):
    """Tests for GET /api/users/me/"""

    def setUp(self) -> None:
        self.url = reverse("users-me")
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="strongpass123",
            first_name="Test",
            last_name="User",
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_me_success(self) -> None:
        """Good case: authenticated → 200"""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(self.refresh.access_token)}"
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_me_without_token(self) -> None:
        """Bad case 1: no token → 401"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_me_invalid_token(self) -> None:
        """Bad case 2: invalid token → 401"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
