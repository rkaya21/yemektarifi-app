# mypy: ignore-errors
"""
Views for the recipe APIs.
"""

from typing import Any

from core.models import Ingredient, Recipe, Tag
from django_filters.rest_framework import DjangoFilterBackend
from recipe import serializers
from rest_framework import filters, mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response


class RecipeViewSet(viewsets.ModelViewSet[Recipe]):  # type: ignore[misc]
    """View for manage recipe APIs."""

    serializer_class = serializers.RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["tags"]
    search_fields = ["title", "description"]
    ordering_fields = ["id", "title", "time_minutes", "price"]

    def get_queryset(self) -> Any:
        """Return recipes for the authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self) -> Any:
        """Return appropriate serializer class."""
        if self.action == "retrieve":
            return serializers.RecipeDetailSerializer
        if self.action == "upload_image":
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer: serializers.RecipeSerializer) -> None:
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request: Request, pk: Any = None) -> Response:
        """Upload an image to a recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):  # type: ignore
    """Manage tags in the database."""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> Any:
        """Return tags for the authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by("-name")

    def perform_create(self, serializer: serializers.TagSerializer) -> None:
        """Create a new tag for the authenticated user."""
        serializer.save(user=self.request.user)


class IngredientViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):  # type: ignore
    """Manage ingredients in the database."""

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> Any:
        """Return ingredients for the authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by("-name")

    def perform_create(self, serializer: serializers.IngredientSerializer) -> None:
        """Create a new ingredient for the authenticated user."""
        serializer.save(user=self.request.user)
