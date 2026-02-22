# Python import 
import logging

# Rest modules
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ValidationError, 
    CharField,
    BooleanField,
    PrimaryKeyRelatedField
)

#Project import
from .models import Channel, ChannelMembership
from apps.team.models import Team
from apps.users.models import CustomUser
from apps.users.serializers import UserListSerializer

logger = logging.getLogger(__name__)

class ChannelSerializer(ModelSerializer):
    """
    Read-only serializer for Channel
    Used in: list, retrieve
    """

    team_name = SerializerMethodField()
    members_count = SerializerMethodField()
    members = UserListSerializer(many=True, read_only=True)

    class Meta:
        model = Channel
        fields = [
            'id',
            'name',
            'description',
            'team',
            'team_name'
            'is_private',
            'members',
            'members_count',
            'create_at',
            'update_at',
        ]

    def get_team_name(self, obj: Channel) -> str:
        """Get team name"""
        return obj.team.name
    
    def get_members_count(self, obj: Channel) -> int:
        """Get count of private channel members"""
        if obj.is_private:
            return obj.members.count()
        # For public channels, count all team members
        return obj.team.members.count()
    

class CreateChannelSerializer(ModelSerializer):
    """
    Serializer for creating a Channel
    User in : create
    """

    name = CharField(
        min_length=1,
        max_length=200,
        trim_whitespace=True
    )

    description = CharField(
        required=False,
        allow_blank=True,
        max_length=1000
    )

    team =  PrimaryKeyRelatedField(
        queryset=Team.objects.all()
    )

    is_private = BooleanField(
        default=False
    )

    class Meta:
        model = Channel
        fields = [
            'name',
            'description',
            'team',
            'is_private',
        ]

    def validate(self, attrs):
        """
        Validate channel data
        """
        team = attrs['team']
        name = attrs['name']

        #Check if channel with this name already exists in team 
        if Channel.objects.filter(team=team, name__iexact=name).exists():
            logger.warning(
                'Channel creation failed - name exists: team=%s name=%s',
                team.id,
                name
            )
            raise ValidationError({
                'name': f"Channel '{name}' already exists in this team."
            })
        
        # Check if user is a member of the team
        request = self.context.get('request')
        if request and request.user:
            # fdfsd
            # if not team.members.filter(id=request.user.id).exists():
            #    raise ValidationError("You must be a team member to create channels")
            pass

        return attrs
    
    def create(self, validated_data):
        """Create channel"""
        request = self.context.get('request')
        channel = Channel.objects.create(**validated_data)

        logger.info(
            'Channel created: id=%s name=%s team%s by user=%s',
            channel.id,
            channel.name,
            channel.team.id,
            request.user.id if request else 'unknown'
        )

        return channel
    

class UpdateChannelSerializer(ModelSerializer):
    """
    Serializer for updating a Channel.
    Used in: update, partial_update
    """

    name = CharField(
        min_length=1,
        max_length=200,
        trim_whitespace=True,
        required=True
    )

    description = CharField(
        required=False,
        allow_blank=True,
        max_length=1000
    )

    is_private = BooleanField(
        required=False
    )

    class Meta:
        model = Channel
        fields = [
            'name',
            'description',
            'is_private',
        ]
    def validate_name(self, value: str) -> str:
        """Validate that name is unique within the team"""
        channel =  self.instance
        qs = Channel.objects.filter(
            team=channel.team,
            name__iexact=value
        ).exclude(pk=channel.pk)

        if qs.exists():
            logger.warning(
                'Channel update failed - name exists: team=%s name=%s',
                channel.team.id,
                value
            )
            raise ValidationError(f"Channel '{value}' already exists in this team")
        
        return value
    
    def update(self, instance: Channel, validated_data: dict) -> Channel:
        """Update channel"""
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.is_private = validated_data.get('is_private', instance.is_private)

        instance.save(update_fields=['name', 'description', 'is_private'])

        logger.info(
            'Channel updated: id=%s name=%s',
            instance.id,
            instance.name
        )

        return instance
    

class ChannelMembershipSerializer(ModelSerializer):
    """
    Read-only serializer for ChannelMember.
    Used in: list
    """

    channel = ChannelSerializer(read_only=True)
    user = UserListSerializer(read_only=True)

    class Meta:
        model = ChannelMembership
        fields = [
            'id',
            'channel',
            'user',
            'joined_at',
        ]


class AddChannelMemberSerializer(ModelSerializer):
    """"
    Serializer for adding a member to private channel.
    Used in: add member action
    """

    class Meta:
        model = ChannelMembership
        fields = [
            'channel',
            'user',
        ]

    def validate(self, attrs):
        """Validate membership"""
        channel = attrs['channel']
        user = attrs['user']

        # Check if channel is private
        if not channel.is_private:
            raise ValidationError({
                'channel': "Can only add members to private channels."
            })
        
        # Check if user is already a member
        if ChannelMembership.objects.filter(channel=channel, user=user).exists():
            logger.warning(
                'Membership already exists: channel=%s user=%s',
                channel.id,
                user.id
            )
            raise ValidationError({
                'user' : "User is already a member of this channel"
            })
        
        # Check if user us a team member
        if not channel.team.members.filter(id=user.id).exists():
            raise ValidationError({
                'user' : "User must be a team member to join this channel."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create channel membership. """
        membership = ChannelMembership.objects.create(**validated_data)

        logger.info(
            'Channel member added: channel=%s user=%s',
            membership.channel.id,
            membership.user.id
        )
        
        return membership
            