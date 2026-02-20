from django.urls import path,include

from .view import TeamViewSet

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'teams',TeamViewSet,basename='team')

urlpatterns = [
    path('',include(router.urls))
]