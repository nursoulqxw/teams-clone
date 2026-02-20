# Python modules
import logging

# Rest modules
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
    CharField,
    IntegerField
)

# Project modules
from .models import Team, TeamMembership
from users.serializers import UserListSerializer

logger = logging.getLogger(__name__)


class TeamSerializer(ModelSerializer):
    """
    Read-only serializer for Team
    Used in: list, retrieve
    """
    owner_info = SerializerMethodField()
    members = UserListSerializer(
        many=True, 
        read_only=True
    )
    members_count = SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'description',
            'owner_info',
            'members',
            'members_count',
        ]

    def get_owner_info(
            self, 
            obj: Team
        ) -> dict:
        owner = obj.owner
        return {
            'id': owner.id,
            'first_name': owner.first_name,
            'last_name': owner.last_name,
        }

    def get_members_count(
            self, 
            obj: Team
        ) -> int:
        return obj.members.count()


class CreateTeamSerializer(ModelSerializer):
    """
    Serializer for creating a Team
    Used in: create
    """
    name = CharField(
        min_length=2, 
        max_length=100, 
        trim_whitespace=True
    )
    description = CharField(
        required=False, 
        allow_blank=True, 
        max_length=500
    )

    class Meta:
        model = Team
        fields = [
            'name',
            'description',
        ]

    def validate_name(
            self, 
            value: str
        ) -> str:
        """
        Validation name
        """

        if Team.objects.filter(name__iexact=value).exists():
            logger.warning('Team creation failed - name already exists: %s', value)

            raise ValidationError("Team with this name already exists.")
        
        return value

    def create(
        self, 
        validated_data: dict
    ) -> Team:
        """Create Team"""

        request = self.context['request']
        logger.info(
            'User %s creating team: %s',
            request.user.id,
            validated_data.get('name')
        )
        return Team.objects.create(
            owner=request.user,
            **validated_data
        )


class UpdateTeamSerializer(ModelSerializer):
    """
    Serializer for updating a Team
    Used in: update, partial_update
    """
    name = CharField(
        min_length=2, 
        max_length=100, 
        trim_whitespace=True, 
        required=False
    )
    description = CharField(
        required=False, 
        allow_blank=True, 
        max_length=500
    )
    
    class Meta:
        model = Team
        fields = [
            'name',
            'description',
        ]

    def validate_name(self, value: str) -> str:
        qs = Team.objects.filter(name__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            logger.warning('Team update failed - name already exists: %s', value)
            raise ValidationError("Team with this name already exists.")
        return value

    def update(
        self, 
        instance: Team, 
        validated_data: dict
    ) -> Team:
        """Update team"""
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save(update_fields=['name', 'description'])

        logger.info('Team updated: id=%s name=%s', instance.id, instance.name)

        return instance


class TeamMembershipSerializer(ModelSerializer):
    """
    Read-only serializer for TeamMembership
    Used in: list, retrieve
    """
    team = TeamSerializer(read_only=True)
    user = UserListSerializer(read_only=True)
    role_display = SerializerMethodField()

    class Meta:
        model = TeamMembership
        fields = [
            'id',
            'team',
            'user',
            'role',
            'role_display',
            'joined_at',
        ]
        read_only_fields = ['joined_at']

    def get_role_display(
        self, 
        obj: TeamMembership
    ) -> str:
        return obj.get_role_display()


class CreateTeamMembershipSerializer(ModelSerializer):
    """
    Serializer for adding a member to a Team
    Used in: create
    """
    class Meta:
        model = TeamMembership
        fields = [
            'team',
            'user',
            'role',
        ]

    def validate(
        self, 
        attrs: dict
    ) -> dict:
        """Validation all team member"""
        team = attrs['team']
        user = attrs['user']

        if TeamMembership.objects.filter(team=team, user=user).exists():
            logger.warning(
                'Membership already exists: user=%s team=%s',
                user.id, team.id
            )
            raise ValidationError({
                'error': "User is already a member of this team."
            })

        return attrs

    def create(
        self, 
        validated_data: dict
    ) -> TeamMembership:
        """Create team member"""
        membership = TeamMembership.objects.create(**validated_data)
        logger.info(
            'Membership created: user=%s team=%s role=%s',
            membership.user.id,
            membership.team.id,
            membership.role
        )
        return membership


class UpdateTeamMembershipSerializer(ModelSerializer):
    """
    Serializer for updating role in TeamMembership
    Used in: update, partial_update
    """
    class Meta:
        model = TeamMembership
        fields = ['role']

    def update(
        self, 
        instance: TeamMembership, 
        validated_data: dict
    ) -> TeamMembership:
        """Update team member"""
        instance.role = validated_data.get('role', instance.role)
        instance.save(update_fields=['role'])
        logger.info(
            'Membership role updated: user=%s team=%s new_role=%s',
            instance.user.id,
            instance.team.id,
            instance.role
        )
        return instance