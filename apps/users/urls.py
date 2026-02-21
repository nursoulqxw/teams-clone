from rest_framework.routers import DefaultRouter
from .views import AuthViewSet

router = DefaultRouter()

router.register(r"", AuthViewSet, basename="users")
urlpatterns = router.urls