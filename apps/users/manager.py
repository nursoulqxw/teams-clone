from typing import Any, TYPE_CHECKING
from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from apps.users.models import CustomUser


class CustomUserManager(BaseUserManager):

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        *args: tuple,
        **kwargs: dict,
    ) -> "CustomUser":

        if not email:
            raise ValueError("Email must be set")

        if not password:
            raise ValueError("Password must be set")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            *args,
            **kwargs,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user


    def create_superuser(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        *args: tuple,
        **kwargs: dict,
    ) -> "CustomUser":

        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_active", True)

        if kwargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if kwargs.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
