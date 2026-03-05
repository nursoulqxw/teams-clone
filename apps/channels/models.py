# Django imports
from django.db import models
from django.db.models import (
    Model,
    CharField,
    TextField,
    AutoField,
    ForeignKey,
    BooleanField,
    CASCADE,
    Index,
    ManyToManyField
)
# Project imports
from apps.abstract.models import AbstractModel
from apps.users.models import CustomUser
from apps.team.models import Team

class  Channel(AbstractModel):
    """
    Model representing a channel within a team
    Channels can be public (all team members) or private(selected members only) 
    """
    id = AutoField(
        primary_key=True
    )

    name = CharField(
        max_length=200,
        help_text="Channel name (e.g., 'general', 'random)"
    )

    description = TextField(
        blank=True,
        null=True,
        help_text="Channel description"
    )

    team = ForeignKey(
        Team,
        on_delete=CASCADE,
        related_name='channels',
        help_text="Parent team"
    )

    is_private = BooleanField(
        default=False,
        help_text="IF True, only selected members can access this channel"
    )

    members = ManyToManyField(
        CustomUser, 
        through='ChannelMembership',
        related_name='private_channels',
        blank=True,
        help_text="Members with access (for private channels only)"
    )

    def __str__(self):
        """
        String representation of the Channel model.
        """
        privacy = "Private" if self.is_private else "Public"
        return f"#{self.name} ({privacy}) - {self.team.name}"
    
    class Meta:
        verbose_name = "Channel"
        verbose_name_plural = "Channels"
        unique_together = ('team', 'name')
        ordering = ['team', 'name']
        indexes = [
            Index(fields=['team']),
            Index(fields=['team', 'name']),
            Index(fields=['is_private']),
        ]


class ChannelMembership(Model):
    """
    Model representing the membership of a user in private channel.
    Only used for private channels
    """

    id  = AutoField(
        primary_key=True
    )

    channel = ForeignKey(
        Channel,
        on_delete=CASCADE,
        related_name='channel_memberships'
    )

    user = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='channel_memberships'
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        """
        String representation of the ChannelMembership model
        """
        return f"{self.user.email} in #{self.channel.name}"
    
    class Meta:
        verbose_name = "Channel Membership"
        verbose_name_plural = "Channel MemberShips"
        unique_together = ('channel', 'user')
        indexes = [
            Index(fields=['channel', 'user']),
        ]