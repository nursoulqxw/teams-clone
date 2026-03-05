from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import AssigmentsViewSet

router = DefaultRouter()
router.register(r'assignment',AssigmentsViewSet,basename='assignment')

urlpatterns = [
    path('',include(router.urls))
]