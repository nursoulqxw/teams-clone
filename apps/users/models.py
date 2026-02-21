from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from apps.abstract.models import AbstractModel
from apps.users.manager import CustomUserManager


class CustomUser(
    AbstractBaseUser,
    AbstractModel,
    PermissionsMixin,
):

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(
        max_length=255,
        blank=True,
    )

    last_name = models.CharField(
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    last_login = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "email"

    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email}"
