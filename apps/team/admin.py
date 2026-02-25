from django.contrib.admin import(
    ModelAdmin,
    register
) 

#Project imports
from apps.team.models import Team,TeamMembership


@register(Team)
class TeamAdmin(ModelAdmin):
    list_display = (
        'id',
        'name', 
        'owner',
    )
    search_fields = (
        'name', 
        'owner__username',
    )
    list_filter = ('owner',)

@register(TeamMembership)
class TeamMembershipAdmin(ModelAdmin):
    list_display = (
        'id', 
        'team', 
        'user', 
        'role',
    )
    search_fields = (
        'team__name', 
        'user__username', 
        'role',
    )
    list_filter = ('role',)

