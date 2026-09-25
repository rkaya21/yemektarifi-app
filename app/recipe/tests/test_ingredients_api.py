"""
Test for the ingredients API endpoints.
"""

from typing import Any, Dict

from core.models import Ingredient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id: int) -> str:
    """Create and return an ingredient detail URL."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email: str = "user@example.com", password: str = "testpass123") -> Any:
    """Helper function to create a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    """Tests for unauthenticated API access to ingredients."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self) -> None:
        """Test auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]

    def test_retrieve_ingredients(self) -> None:
        """Test retrieving ingredients."""
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Vanilla")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)  # type: ignore[attr-defined]
        self.assertIn("next", res.data)  # type: ignore[attr-defined]
        self.assertIn("previous", res.data)  # type: ignore[attr-defined]
        self.assertEqual(res.data["count"], ingredients.count())  # type: ignore[index]
        self.assertEqual(  # type: ignore[index]
            res.data["results"],
            serializer.data,
        )

    def test_ingredients_limited_to_user(self) -> None:
        """Test list of ingredients is limited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        Ingredient.objects.create(user=user2, name="Salt")
        ingredient = Ingredient.objects.create(user=self.user, name="Pepper")

        res = self.client.get(INGREDIENTS_URL)
        data: Dict[str, Any] = res.data  # type: ignore[attr-defined]

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["name"], ingredient.name)
        self.assertEqual(data["results"][0]["id"], ingredient.id)

    def test_update_ingredient(self) -> None:
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Cilantro")

        payload = {"name": "Coriander"}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self) -> None:
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Lettuce")
        ingredient_id = ingredient.id

        url = detail_url(ingredient_id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient_id).exists())

    def test_create_ingredient(self) -> None:
        """Test creating a new ingredient."""
        payload = {"name": "Domates"}

        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ingredient = Ingredient.objects.get(id=res.data["id"])  # type: ignore[index]
        self.assertEqual(ingredient.name, payload["name"])
        self.assertEqual(ingredient.user, self.user)
