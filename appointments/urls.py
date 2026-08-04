from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import AppointmentViewSet

app_name = "appointments"

router = SimpleRouter()
router.register(r"", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
]