# isort: skip_file
"""
app URL Configuration

The `urlpatterns` list routes URLs to views. For more information, please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # OpenAPI Schema Endpoint
    # Serves the OpenAPI schema in JSON format.
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    # Swagger UI
    # Interactive API docs for testing endpoints in the browser.
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    # Redoc
    # Alternative API documentation interface based on the OpenAPI schema.
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="api-schema"),
        name="api-redoc",
    ),
    path("api/user/", include("user.urls")),
    path("api/recipe/", include("recipe.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
