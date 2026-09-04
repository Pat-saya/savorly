from dataclasses import dataclass
import re

import requests
from flask import current_app


class RecipeAPIError(RuntimeError):
    pass


@dataclass
class Recipe:
    id: str
    name: str
    image_url: str | None
    category: str | None
    cuisine: str | None
    instructions: str
    ingredients: list[tuple[str, str]]
    source_url: str | None
    video_url: str | None


def _request(endpoint, **params):
    base = current_app.config["MEALDB_BASE_URL"].rstrip("/")
    key = current_app.config["MEALDB_API_KEY"]
    try:
        response = requests.get(f"{base}/{key}/{endpoint}", params=params, timeout=8)
        response.raise_for_status()
        return response.json().get("meals") or []
    except (requests.RequestException, ValueError, AttributeError) as exc:
        current_app.logger.warning("TheMealDB request failed: %s", exc)
        raise RecipeAPIError("Recipe search is temporarily unavailable. Please try again.") from exc


def normalize(meal):
    ingredients = []
    for number in range(1, 21):
        ingredient = (meal.get(f"strIngredient{number}") or "").strip()
        measure = (meal.get(f"strMeasure{number}") or "").strip()
        if ingredient:
            ingredients.append((measure, ingredient))
    return Recipe(
        id=str(meal["idMeal"]), name=meal["strMeal"], image_url=meal.get("strMealThumb"),
        category=meal.get("strCategory"), cuisine=meal.get("strArea"),
        instructions=meal.get("strInstructions") or "", ingredients=ingredients,
        source_url=meal.get("strSource"), video_url=meal.get("strYoutube"),
    )


def _normalize_search_text(value):
    """Normalize harmless separators while preserving meaningful words."""
    return " ".join(re.sub(r"[-_]+", " ", value.casefold()).split())


def _joined_search_text(value):
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def search_recipes(query):
    query = _normalize_search_text(query)
    meals = _request("search.php", s=query)
    # TheMealDB name search does not match joined words such as "padthai".
    # Try each possible single-space split and accept only exact joined-name
    # matches, avoiding broad fuzzy results that merely look similar.
    if not meals and " " not in query and 3 < len(query) <= 30:
        joined_query = _joined_search_text(query)
        for position in range(2, len(query) - 1):
            candidates = _request("search.php", s=f"{query[:position]} {query[position:]}")
            meals = [meal for meal in candidates if _joined_search_text(meal.get("strMeal", "")) == joined_query]
            if meals:
                break
    return [normalize(meal) for meal in meals]


def list_areas():
    return sorted(
        (meal["strArea"] for meal in _request("list.php", a="list") if meal.get("strArea")),
        key=str.casefold,
    )


def list_categories():
    return sorted(
        (meal["strCategory"] for meal in _request("list.php", c="list") if meal.get("strCategory")),
        key=str.casefold,
    )


def browse_area(area):
    recipes = [normalize(meal) for meal in _request("filter.php", a=area)]
    for recipe in recipes:
        recipe.cuisine = recipe.cuisine or area
    return recipes


def browse_category(category):
    recipes = [normalize(meal) for meal in _request("filter.php", c=category)]
    for recipe in recipes:
        recipe.category = recipe.category or category
    return recipes


def get_recipe(recipe_id):
    meals = _request("lookup.php", i=recipe_id)
    return normalize(meals[0]) if meals else None
