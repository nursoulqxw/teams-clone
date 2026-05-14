#Django import
from django.db.models import (
    Model,
    TextField,
    BigAutoField, #Same idea but bigger range. supports HUGE ids
    AutoField, # Auto-increment integer primary key.
    ForeignKey,
    CASCADE, #If parent is deleted → delete children automatically. 
    Index, #“Make search faster.”
    DateTimeField,
)
from django.utils.translation import gettext_lazy as _

#Project import 
from apps.users.models import CustomUser
from apps.channels.models import Channel

# Create your models here.
class Message(Model):
    content = TextField(
        verbose_name=_("content")
    )
    #connections
    author = ForeignKey(
        CustomUser,
        on_delete=CASCADE, #Defines what happens when the referenced object is deleted(on_delete).
        related_name='author_messages',
        verbose_name=_("author")
    )
    channel = ForeignKey(
        Channel,
        on_delete=CASCADE,
        related_name='channel_messages',
        verbose_name=_("channel"),
    )
    #for the thread/answers realisiation
    parent_message = ForeignKey(
        'self',
        on_delete=CASCADE,
        null=True, #Allows storing NULL in DB.
        blank=True, #Allows field to be empty during validation.
        related_name='replies', #Creates reverse access.
        verbose_name=_("parent message"),
    )

    created_at = DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at")
    ) #Set once when created.
    updated_at = DateTimeField(
        auto_now=True,
        verbose_name=_("updated at")
    ) #Updates automatically every save.

    class Meta:
        verbose_name = _("Message")          
        verbose_name_plural = _("Messages")
        ordering = ['created_at']
        indexes = [
            Index(fields=['channel', '-created_at']),
            Index(fields=['author']),
            Index(fields=['parent_message']),
        ]