from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.channels.views import ChannelViewSet

router = DefaultRouter()
router.register(r'', ChannelViewSet, basename='channel')

urlpatterns = [
    path('', include(router.urls))
]