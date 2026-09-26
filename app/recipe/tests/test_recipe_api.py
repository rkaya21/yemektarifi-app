"""
Tests for recipe API endpoints.
"""

import os
import tempfile
from decimal import Decimal
from typing import Any, Dict

from core.models import Ingredient, Recipe, Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id: int) -> str:
    """Create and return a recipe detail URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id: int) -> str:
    """Create and return an image upload URL."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user: Any, **params: Any) -> Recipe:
    """Create and return a sample recipe."""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params: Any) -> Any:
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        """Test auth is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testpass123")
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]

    def test_retrieve_recipes(self) -> None:
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)  # type: ignore[attr-defined]
        self.assertIn("next", res.data)  # type: ignore[attr-defined]
        self.assertIn("previous", res.data)  # type: ignore[attr-defined]
        self.assertEqual(res.data["count"], recipes.count())  # type: ignore[index]
        self.assertEqual(  # type: ignore[index]
            res.data["results"],
            serializer.data,
        )

    def test_recipe_list_limited_to_user(self) -> None:
        """
        Test list of recipes is
        limited to authenticated user.
        """
        other_user = create_user(email="other@example.com", password="password123")
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], recipes.count())  # type: ignore[index]
        self.assertEqual(  # type: ignore[index]
            res.data["results"],
            serializer.data,
        )

    def test_get_recipe_detail(self) -> None:
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)  # type: ignore[attr-defined]

    def test_create_recipe(self) -> None:
        """Test creating a recipe."""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.99"),
            "description": "Delicious chocolate cheesecake recipe",
            "link": "http://example.com/chocolate_cheesecake.pdf",
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data: Dict[str, Any] = res.data  # type: ignore[attr-defined]
        recipe = Recipe.objects.get(id=data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self) -> None:
        """Test partial update of a recipe."""
        original_link = "http://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link=original_link,
        )

        payload = {"title": "New recipe title"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self) -> None:
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link="http://example.com/recipe.pdf",
            description="Sample description",
        )

        payload = {
            "title": "New recipe title",
            "time_minutes": 10,
            "price": Decimal("2.50"),
            "description": "New recipe description",
            "link": "http://example.com/new-recipe.pdf",
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self) -> None:
        """
        Test changing the recipe
        user resulsts in an error.
        """
        new_user = create_user(email="user2@example.com", password="testpass123")
        recipe = create_recipe(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self) -> None:
        """Test deleting a recipe successful."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self) -> None:
        """
        Test trying to delete another
        users recipe gives error.
        """
        new_user = create_user(email="user2@example.com", password="testpass123")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self) -> None:
        """Test creating a recipe with new tags."""
        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        tags_payload: Any = payload["tags"]
        for tag in tags_payload:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self) -> None:
        """Test creating a recipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name="Indian")
        payload = {
            "title": "Pongal",
            "time_minutes": 60,
            "price": Decimal("4.50"),
            "tags": [{"name": "Indian"}, {"name": "Breakfast"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        tags_payload: Any = payload["tags"]
        for tag in tags_payload:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_new_ingredients(self) -> None:
        """Test creating a recipe with new ingredients."""
        payload = {
            "title": "Cauliflower Tacos",
            "time_minutes": 60,
            "price": Decimal("4.30"),
            "ingredients": [{"name": "Cauliflower"}, {"name": "Salt"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        ingredients_payload: Any = payload["ingredients"]
        for ingredient in ingredients_payload:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self) -> None:
        """Test creating a recipe with an existing ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Lemon")
        payload = {
            "title": "Vietnamese Soup",
            "time_minutes": 25,
            "price": Decimal("2.55"),
            "ingredients": [{"name": "Lemon"}, {"name": "Fish Sauce"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        ingredients_payload: Any = payload["ingredients"]
        for ing in ingredients_payload:
            exists = recipe.ingredients.filter(
                name=ing["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_filter_recipes_by_tags(self) -> None:
        """Test filtering recipes by tag."""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        tag1 = Tag.objects.create(user=self.user, name="Dinner")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        res = self.client.get(RECIPES_URL, {"tags": tag1.id})

        serializer = RecipeSerializer([recipe1], many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)  # type: ignore[index]
        self.assertEqual(res.data["results"], serializer.data)  # type: ignore[index]

    def test_filter_recipes_by_ingredients(self) -> None:
        """Test filtering recipes by ingredient."""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        ingredient1 = Ingredient.objects.create(user=self.user, name="Feta")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Chicken")
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        res = self.client.get(RECIPES_URL, {"ingredients": ingredient1.id})

        serializer = RecipeSerializer([recipe1], many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)  # type: ignore[index]
        self.assertEqual(res.data["results"], serializer.data)  # type: ignore[index]

    def test_search_recipes(self) -> None:
        """Test searching recipes by title and description."""
        recipe1 = create_recipe(
            user=self.user,
            title="Thai Coconut Curry",
            description="Curry with coconut milk",
        )
        recipe2 = create_recipe(
            user=self.user,
            title="Avocado Toast",
            description="Breakfast with avocado",
        )

        res = self.client.get(RECIPES_URL, {"search": "coconut"})

        serializer = RecipeSerializer([recipe1], many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)  # type: ignore[index]
        self.assertEqual(res.data["results"], serializer.data)  # type: ignore[index]

        res = self.client.get(RECIPES_URL, {"search": "toast"})
        serializer = RecipeSerializer([recipe2], many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)  # type: ignore[index]
        self.assertEqual(res.data["results"], serializer.data)  # type: ignore[index]

    def test_ordering_recipes(self) -> None:
        """Test ordering recipes by time."""
        create_recipe(user=self.user, title="Recipe 1", time_minutes=20)
        create_recipe(user=self.user, title="Recipe 2", time_minutes=10)

        res = self.client.get(RECIPES_URL, {"ordering": "time_minutes"})

        recipes = Recipe.objects.filter(user=self.user).order_by("time_minutes")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)  # type: ignore[index]


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testpass123")
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self) -> None:
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)  # type: ignore[attr-defined]
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self) -> None:
        """Test uploading an invalid image returns a bad request."""
        url = image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
