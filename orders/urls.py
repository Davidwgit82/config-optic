from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import OrderViewSet

app_name = "orders"

router = SimpleRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
]