from typing import Any

from django.db.models import Model,DateTimeField
from django.utils import timezone as django_timezone


class AbstractModel(Model):
    create_at = DateTimeField(
        auto_now_add=True,
    )
    update_at = DateTimeField(
        auto_now=True,
    )
    delete_at = DateTimeField(
        null=True,
        blank=True,
        default=None,
    )
    class Meta:
        abstract = True
    def delete(self, using: Any = None, keep_parents: bool = False) -> None:
        self.delete_at = django_timezone.now()
        self.save( update_fields=["delete_at"] )



