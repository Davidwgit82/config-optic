from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    path("users/", include("users.urls", namespace="users")),
    path("catalog/", include("catalog.urls", namespace="catalog")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("appointments/", include("appointments.urls", namespace="appointments")),
    path("payments/", include("payments.urls", namespace="payments")), 
]

urlpatterns = [
    # Administration Django
    path("admin/", admin.site.urls),

    # Endpoints API v1
    path("api/v1/", include((api_v1_patterns, "v1"))),

    # --- Documentation API (OpenAPI 3 / Swagger / ReDoc) ---
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Debug Toolbar & Fichiers Média (en développement)
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
