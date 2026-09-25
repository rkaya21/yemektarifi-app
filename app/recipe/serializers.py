"""
Serializers for Recipe APIs
"""

from typing import Any, Dict, List

from core.models import Ingredient, Recipe, Tag
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer[Tag]):  # type: ignore[misc]
    """Serializer for Tag objects"""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class IngredientSerializer(
    serializers.ModelSerializer[Ingredient]  # type: ignore[misc]
):
    """Serializer for Ingredient objects"""

    class Meta:
        model = Ingredient
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer[Recipe]):  # type: ignore[misc]
    """Serializer for Recipe objects"""

    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "time_minutes",
            "price",
            "link",
            "tags",
            "ingredients",
            "description",
            "image",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data: Dict[str, Any]) -> Recipe:
        """create a recipe"""
        tags: List[Dict[str, Any]] = validated_data.pop("tags", [])
        ingredients: List[Dict[str, Any]] = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user, **ingredient
            )
            recipe.ingredients.add(ingredient_obj)

        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for Recipe detail view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields


class RecipeImageSerializer(serializers.ModelSerializer[Recipe]):  # type: ignore[misc]
    """Serializer for uploading images to recipes."""

    class Meta:
        model = Recipe
        fields = ["id", "image"]
        read_only_fields = ["id"]
        extra_kwargs = {"image": {"required": True}}
