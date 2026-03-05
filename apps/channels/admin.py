from django.contrib import admin
from .models import Channel, ChannelMembership

#1. Create an inline class for participants
class ChannelMembershipInline(admin.TabularInline):
    model = ChannelMembership
    extra = 1 # Shows one empty line to add a new member
    readonly_fields = ['joined_at']
    # autocomplete_fields = ['user'] # Very useful if there are many users

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'team',
        'is_private',
        'create_at',
    ]
    list_filter = ['is_private', 'team']
    search_fields = ['name', 'description', 'team__name']
    readonly_fields = ['create_at', 'update_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'team')
        }),
        ('Settings', {
            # 'fields': ('is_private', 'members')
            'fields': ('is_private',)
        }),
        ('Timestamps', {
            'fields': ('create_at', 'update_at'),
            'classes': ('collapse',)
        }),
    )
    
    #filter_horizontal = ['members']
    # 2. CONNECT INLINE HERE:
    inlines = [ChannelMembershipInline]

@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'channel',
        'user',
        'joined_at',
    ]
    list_filter = ['channel__team', 'joined_at']
    search_fields = ['channel__name', 'user__email']
    readonly_fields = ['joined_at']