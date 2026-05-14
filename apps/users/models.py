from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _

from apps.abstract.models import AbstractModel
from apps.users.manager import CustomUserManager


class CustomUser(
    AbstractBaseUser,
    AbstractModel,
    PermissionsMixin,
):

    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(
        _("first name"),
        max_length=255,
        blank=True,
    )

    last_name = models.CharField(
        _("last name"),
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        _("active"),
        default=True,
    )

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
    )

    date_joined = models.DateTimeField(
        _("date joined"),
        auto_now_add=True,
    )

    last_login = models.DateTimeField(
        _("last login"),
        auto_now=True,
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "email"

    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")           
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.email}"
