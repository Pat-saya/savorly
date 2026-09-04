def test_public_pages_render(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Vegetarian"])
    home = client.get("/")
    assert b"Find dinner" in home.data
    assert b"Savorly" in home.data
    assert b"Not sure what to cook?" in home.data
    assert b"Explore recipes from around the world" in home.data
    assert b"From inspiration to dinner." in home.data
    discover = client.get("/recipes")
    assert b"What are you craving" in discover.data
    assert b'name="category"' in discover.data
    assert b'name="area"' not in discover.data
    assert b"Popular cuisines" not in discover.data


def test_browse_page_uses_only_supported_preferred_options(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: ["Beef", "Seafood", "Vegan", "Vegetarian"])
    response = client.get("/browse")
    assert response.status_code == 200
    assert b"Seafood" in response.data and b"Vegan" in response.data
    assert b"Vegetarian" in response.data
    assert b"Beef" not in response.data
    assert b"By cuisine" not in response.data


def test_browse_page_accepts_trailing_slash(client, monkeypatch):
    monkeypatch.setattr("mealmate.main.list_categories", lambda: [])

    response = client.get("/browse/")

    assert response.status_code == 200
    assert b"Find something worth savoring" in response.data


def test_not_found_uses_friendly_page(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert b"couldn&#39;t find" in response.data


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
