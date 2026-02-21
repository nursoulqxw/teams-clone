
#Django imports
from django.db.models import (
    Model,
    CharField,
    TextField,
    AutoField,
    ForeignKey,
    CASCADE,
    Index,
    DateTimeField,
    ManyToManyField
)

#Project imports
from apps.users.models import CustomUser


class Team(Model):
    """Model representing a team."""

    id = AutoField(
        primary_key=True
    )
    name = CharField(
        max_length=255,
        unique=True
    )
    description = TextField(
        blank=True,
        null=True
    )
    owner = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='owned_teams'
    )
    members = ManyToManyField(
        CustomUser,
        through='TeamMembership',
        related_name='members'
    )

    def __str__(self):
        """String representation of the Team model."""
        return f"Team: {self.name}, Owner: {self.owner.first_name}"
    
    def to_presentation(self):
        """Convert the Team instance to a presentation format."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner': self.owner.first_name,
            'members': [member.first_name for member in self.members.all()]
        }
    
    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        indexes = [
            Index(fields=['name']),
            Index(fields=['owner']),
        ]


class TeamMembership(Model):
    """
    Model representing the membership of a user in a team.
    """
    id = AutoField(
        primary_key=True
    )
    team = ForeignKey(
        Team,
        on_delete=CASCADE,
        related_name='team_memberships'
    )
    user = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='user_memberships'
    )
    joined_at = DateTimeField(
        auto_now_add=True
    )
    role = CharField(
        max_length=150,
        default='member',
        choices=[
            {'admin', 'Admin'},
            {'member', 'Member'},
        ]
    )

    def __str__(self):
        """String representation of the TeamMembership model."""
        return f"TeamMembership: {self.user.first_name} in {self.team.name}"
    
    class Meta:
        verbose_name = "Team Membership"
        verbose_name_plural = "Team Memberships"
        unique_together = ('team', 'user')
        indexes = [
            Index(fields=['team','user']),
        ]