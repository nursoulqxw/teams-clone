# apps/channels/filters.py
import django_filters
from .models import Channel

class ChannelFilter(django_filters.FilterSet):
    # Поиск по name без учета регистра
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Channel
        fields = ['team', 'is_private', 'name']