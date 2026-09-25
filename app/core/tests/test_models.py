"""
Tests for models
"""

from decimal import Decimal
from typing import Any
from unittest.mock import patch

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase


def create_user(email: str = "user@example.com", password: str = "testpass123") -> Any:
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_succesful(self) -> None:
        """Test creating a user"""
        email = "test@gmail.com"
        password = "test123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self) -> None:
        """Check that the system normalizes email addresses for new users."""
        sample_emails = [
            ["test1@GMAIL.com", "test1@gmail.com"],
            ["Test2@Gmail.com", "Test2@gmail.com"],
            ["TEST3@GMAIL.com", "TEST3@gmail.com"],
            ["test4@gmail.COM", "test4@gmail.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "example123")
            self.assertEqual(user.email, expected)

    def test_user_creation_fails_without_email(self) -> None:
        """
        Confirm that creating a user without
        an email results in a ValueError.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_create_superuser(self) -> None:
        """Test create a superuser."""
        user = get_user_model().objects.create_superuser(
            "test@gmail.com",
            "test123",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self) -> None:
        """Test creating a recipe is successful."""
        user = get_user_model().objects.create_user(
            "test@gmail.com",
            "test123",
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Test Recipe",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Test Description",
        )

        self.assertEqual(str(recipe), recipe.title)
        self.assertIsNotNone(recipe.created_at)
        self.assertIsNotNone(recipe.updated_at)

    def test_create_tag(self) -> None:
        """Test creating a tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)
        self.assertIsNotNone(tag.created_at)
        self.assertIsNotNone(tag.updated_at)

    def test_create_ingredient(self) -> None:
        """Test creating an ingredient is successful."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(user=user, name="Salt")

        self.assertEqual(str(ingredient), ingredient.name)
        self.assertIsNotNone(ingredient.created_at)
        self.assertIsNotNone(ingredient.updated_at)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid: Any) -> None:
        """Test generating image path with a UUID filename."""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
