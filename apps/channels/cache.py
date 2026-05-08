# apps/channels/cache.py
from ast import pattern

from django.core.cache import cache, caches

def invalidate_channel_cache(channel_id):
    """Clears the cache for a specific channel."""
    cache.delete(f'channel_{channel_id}')

def invalidate_team_channels_cache(team_id):
    """Clears all channel list caches for a team (all users)"""
    # We use the pattern since the key contains user_id
    #pattern = f"channels_team_{team_id}_user_*"
    #cache.delete_pattern(pattern)
    cache.delete_pattern(f"channels_team_{team_id}_*")