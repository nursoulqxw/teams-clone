# Django REST Framework
from rest_framework.routers import DefaultRouter

# Project modules
from .views import MessageViewSet

router = DefaultRouter()
router.register(r"messages", MessageViewSet, basename="messages")

urlpatterns = router.urls
