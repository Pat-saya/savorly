import pytest
import requests
from mealmate.recipe_api import (
    RecipeAPIError, browse_area, browse_category, get_recipe, list_areas,
    list_categories, search_recipes
)

MEAL = {"idMeal": "42", "strMeal": "Test Curry", "strMealThumb": "https://img.test/curry.jpg", "strCategory": "Curry", "strArea": "Indian", "strInstructions": "Cook it.", "strIngredient1": "Rice", "strMeasure1": "1 cup", "strIngredient2": "", "strMeasure2": "", "strSource": None, "strYoutube": None}

class FakeResponse:
    def raise_for_status(self): pass
    def json(self): return {"meals": [MEAL]}

def test_search_normalizes_meals(app, monkeypatch):
    monkeypatch.setattr("mealmate.recipe_api.requests.get", lambda *args, **kwargs: FakeResponse())
    with app.app_context(): recipes = search_recipes("curry")
    assert recipes[0].name == "Test Curry"
    assert recipes[0].ingredients == [("1 cup", "Rice")]

def test_lookup_returns_none_for_empty_result(app, monkeypatch):
    class EmptyResponse(FakeResponse):
        def json(self): return {"meals": None}
    monkeypatch.setattr("mealmate.recipe_api.requests.get", lambda *args, **kwargs: EmptyResponse())
    with app.app_context(): assert get_recipe("missing") is None

def test_network_error_becomes_domain_error(app, monkeypatch):
    def fail(*args, **kwargs): raise requests.Timeout()
    monkeypatch.setattr("mealmate.recipe_api.requests.get", fail)
    with app.app_context(), pytest.raises(RecipeAPIError): search_recipes("curry")


@pytest.mark.parametrize("query", ["Pad Thai", "pad thai", "PAD THAI", "PadThai", "padthai", "pad-thai", "  pad   thai  "])
def test_pad_thai_search_variants(app, monkeypatch, query):
    searches = []
    def fake_request(endpoint, **params):
        searches.append(params["s"])
        return [{**MEAL, "strMeal": "Pad Thai"}] if params["s"] == "pad thai" else []
    monkeypatch.setattr("mealmate.recipe_api._request", fake_request)
    with app.app_context(): recipes = search_recipes(query)
    assert recipes[0].name == "Pad Thai"
    assert searches[-1] == "pad thai"


def test_normal_existing_search_is_preserved(app, monkeypatch):
    monkeypatch.setattr("mealmate.recipe_api._request", lambda endpoint, **params: [MEAL] if params["s"] == "curry" else [])
    with app.app_context(): recipes = search_recipes(" Curry ")
    assert recipes[0].name == "Test Curry"


def test_nonexistent_joined_search_stays_empty(app, monkeypatch):
    monkeypatch.setattr("mealmate.recipe_api._request", lambda endpoint, **params: [])
    with app.app_context(): recipes = search_recipes("zzznosuchrecipe")
    assert recipes == []


def test_joined_fallback_rejects_unrelated_partial_match(app, monkeypatch):
    def fake_request(endpoint, **params):
        return [MEAL] if " " in params["s"] else []
    monkeypatch.setattr("mealmate.recipe_api._request", fake_request)
    with app.app_context(): recipes = search_recipes("testcurryextra")
    assert recipes == []


def test_areas_and_area_browse_use_api_data(app, monkeypatch):
    def fake_request(endpoint, **params):
        if endpoint == "list.php": return [{"strArea": "Thai"}, {"strArea": "American"}]
        return [{"idMeal": "42", "strMeal": "Pad Thai", "strMealThumb": "image"}]
    monkeypatch.setattr("mealmate.recipe_api._request", fake_request)
    with app.app_context():
        assert list_areas() == ["American", "Thai"]
        recipes = browse_area("Thai")
    assert recipes[0].name == "Pad Thai"
    assert recipes[0].cuisine == "Thai"


def test_categories_and_category_browse_use_api_data(app, monkeypatch):
    def fake_request(endpoint, **params):
        if endpoint == "list.php": return [{"strCategory": "Vegan"}, {"strCategory": "Chicken"}]
        return [{"idMeal": "42", "strMeal": "Vegan Dish", "strMealThumb": "image"}]
    monkeypatch.setattr("mealmate.recipe_api._request", fake_request)
    with app.app_context():
        assert list_categories() == ["Chicken", "Vegan"]
        recipes = browse_category("Vegan")
    assert recipes[0].name == "Vegan Dish"
    assert recipes[0].category == "Vegan"


def test_search_route_handles_empty_results(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Vegan"])
    monkeypatch.setattr("mealmate.main.search_recipes", lambda query: [])
    response = client.get("/recipes?q=definitelymissing")
    assert response.status_code == 200
    assert b"No recipes found" in response.data


def test_search_route_handles_api_error(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Vegan"])
    def fail(_query): raise RecipeAPIError("Recipe search is temporarily unavailable.")
    monkeypatch.setattr("mealmate.main.search_recipes", fail)
    response = client.get("/recipes?q=chicken")
    assert response.status_code == 200
    assert b"temporarily unavailable" in response.data


def test_missing_recipe_detail_is_404(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.get_recipe", lambda recipe_id: None)
    assert client.get("/recipes/missing").status_code == 404


def test_recipe_detail_has_native_print_and_share_actions(client, monkeypatch):
    recipe = type("Recipe", (), {
        "id": "42", "name": "Pad Thai", "image_url": "image", "category": "Noodles",
        "cuisine": "Thai", "instructions": "Cook it.", "ingredients": [("1 cup", "Noodles")],
        "source_url": "https://example.com/recipe", "video_url": None,
    })()
    monkeypatch.setattr("mealmate.main.get_recipe", lambda recipe_id: recipe)
    response = client.get("/recipes/42")
    assert response.status_code == 200
    assert b"Back to recipes" in response.data
    assert b'href="/recipes"' in response.data
    assert b"data-print-recipe" in response.data
    assert b"data-share-recipe" in response.data
    assert b"mailto:" in response.data
    assert b"data-copy-recipe-url" in response.data


def test_recipe_detail_preserves_safe_results_return_to(client, monkeypatch):
    recipe = type("Recipe", (), {
        "id": "42", "name": "Pad Thai", "image_url": "image", "category": "Noodles",
        "cuisine": "Thai", "instructions": "Cook it.", "ingredients": [("1 cup", "Noodles")],
        "source_url": None, "video_url": None,
    })()
    monkeypatch.setattr("mealmate.main.get_recipe", lambda recipe_id: recipe)
    response = client.get("/recipes/42", query_string={"return_to": "/recipes?q=padthai&category=Seafood"})
    assert response.status_code == 200
    assert b'href="/recipes?q=padthai&amp;category=Seafood"' in response.data


def test_recipe_detail_rejects_unsafe_return_to(client, monkeypatch):
    recipe = type("Recipe", (), {
        "id": "42", "name": "Pad Thai", "image_url": "image", "category": "Noodles",
        "cuisine": "Thai", "instructions": "Cook it.", "ingredients": [("1 cup", "Noodles")],
        "source_url": None, "video_url": None,
    })()
    monkeypatch.setattr("mealmate.main.get_recipe", lambda recipe_id: recipe)
    for unsafe in ("https://evil.example/", "//evil.example/", "/recipes/99", "/my/saved"):
        response = client.get("/recipes/42", query_string={"return_to": unsafe})
        assert response.status_code == 200
        assert b'href="/recipes"' in response.data
        assert f'href="{unsafe}"'.encode() not in response.data


def test_search_results_link_includes_return_to(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Vegan"])
    monkeypatch.setattr("mealmate.main.search_recipes", lambda query: [
        type("Recipe", (), {"id": "42", "name": "Pad Thai", "image_url": "image",
                            "cuisine": "Thai", "category": "Noodles"})()
    ])
    response = client.get("/recipes?q=padthai")
    assert response.status_code == 200
    assert b"return_to=" in response.data
    assert b"padthai" in response.data

def test_area_filter_matches_names_without_spaces(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Vegan"])
    monkeypatch.setattr("mealmate.main.browse_area", lambda area: [
        type("Recipe", (), {"id": "42", "name": "Pad Thai", "image_url": "image",
                            "cuisine": "Thai", "category": None})()
    ])
    response = client.get("/recipes?area=Thai&q=padthai")
    assert response.status_code == 200
    assert b"Pad Thai" in response.data
    assert b"in Thai cuisine" in response.data


def test_indian_area_query_is_passed_to_area_filter_and_rendered(client, monkeypatch):
    requested_areas = []
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Vegan"])

    def fake_browse_area(area):
        requested_areas.append(area)
        return [type("Recipe", (), {
            "id": "42", "name": "Test Curry", "image_url": "image",
            "cuisine": "Indian", "category": "Curry",
        })()]

    monkeypatch.setattr("mealmate.main.browse_area", fake_browse_area)
    response = client.get("/recipes?area=Indian")

    assert response.status_code == 200
    assert requested_areas == ["Indian"]
    assert b"Test Curry" in response.data
    assert b"in Indian cuisine" in response.data


def test_category_filter_uses_category_endpoint(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Vegan"])
    monkeypatch.setattr("mealmate.main.browse_category", lambda category: [
        type("Recipe", (), {"id": "42", "name": "Vegan Lasagna", "image_url": "image",
                            "cuisine": None, "category": "Vegan"})()
    ])
    response = client.get("/recipes?category=Vegan")
    assert response.status_code == 200
    assert b"Vegan Lasagna" in response.data
    assert b"in Vegan" in response.data
