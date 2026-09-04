from mealmate.extensions import db
from mealmate.models import Collection, MealPlan, SavedRecipe, User
from mealmate.recipe_api import Recipe

def fake_recipe(): return Recipe("42", "Test Curry", "https://img.test/curry.jpg", "Curry", "Indian", "Cook.", [("1 cup", "Rice")], None, None)

def test_save_note_collection_and_plan(app, login, monkeypatch):
    monkeypatch.setattr("mealmate.user_data.get_recipe", lambda recipe_id: fake_recipe())
    assert login.post("/my/saved/42").status_code == 302
    with app.app_context(): recipe_id = db.session.scalar(db.select(SavedRecipe.id))
    login.post(f"/my/saved/{recipe_id}/note", data={"note": "Less salt"})
    login.post("/my/collections", data={"name": "Weeknight"})
    login.post("/my/plans", data={"name": "This week"})
    with app.app_context():
        collection_id = db.session.scalar(db.select(Collection.id)); plan_id = db.session.scalar(db.select(MealPlan.id))
    login.post(f"/my/collections/{collection_id}/recipes", data={"saved_recipe_id": recipe_id})
    login.post(f"/my/plans/{plan_id}/items", data={"saved_recipe_id": recipe_id, "planned_for": "2026-09-04", "meal_type": "Dinner"})
    with app.app_context():
        recipe = db.session.get(SavedRecipe, recipe_id)
        assert recipe.note == "Less salt"
        assert recipe in db.session.get(Collection, collection_id).recipes
        assert db.session.get(MealPlan, plan_id).items[0].recipe == recipe

def test_user_cannot_access_another_users_collection(app, login):
    with app.app_context():
        other = User(username="other", email="other@example.com"); other.set_password("password2")
        db.session.add(other); db.session.flush()
        collection = Collection(user_id=other.id, name="Private"); db.session.add(collection); db.session.commit(); collection_id = collection.id
    assert login.get(f"/my/collections/{collection_id}").status_code == 403


def test_saving_same_external_recipe_twice_is_idempotent(app, login, monkeypatch):
    monkeypatch.setattr("mealmate.user_data.get_recipe", lambda recipe_id: fake_recipe())
    login.post("/my/saved/42")
    response = login.post("/my/saved/42", follow_redirects=True)
    assert b"already saved" in response.data
    with app.app_context():
        assert len(db.session.scalars(db.select(SavedRecipe)).all()) == 1


def test_user_cannot_mutate_another_users_recipe(app, login):
    with app.app_context():
        other = User(username="other2", email="other2@example.com"); other.set_password("password2")
        db.session.add(other); db.session.flush()
        recipe = SavedRecipe(user_id=other.id, external_id="99", name="Private recipe")
        db.session.add(recipe); db.session.commit(); recipe_id = recipe.id
    assert login.post(f"/my/saved/{recipe_id}/note", data={"note": "tamper"}).status_code == 403
    assert login.post(f"/my/saved/{recipe_id}/delete").status_code == 403


def test_missing_plan_date_is_validation_error(app, login):
    with app.app_context():
        user_id = db.session.scalar(db.select(User.id).where(User.username == "chef"))
        recipe = SavedRecipe(user_id=user_id, external_id="42", name="Test")
        plan = MealPlan(user_id=user_id, name="Week")
        db.session.add_all([recipe, plan]); db.session.commit(); recipe_id, plan_id = recipe.id, plan.id
    response = login.post(f"/my/plans/{plan_id}/items", data={"saved_recipe_id": recipe_id}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Choose a valid date" in response.data


def test_empty_rename_has_helpful_validation(app, login):
    with app.app_context():
        user_id = db.session.scalar(db.select(User.id).where(User.username == "chef"))
        collection = Collection(user_id=user_id, name="Favorites")
        plan = MealPlan(user_id=user_id, name="This week")
        db.session.add_all([collection, plan]); db.session.commit()
        collection_id, plan_id = collection.id, plan.id
    collection_response = login.post(f"/my/collections/{collection_id}/edit", data={"name": " "}, follow_redirects=True)
    plan_response = login.post(f"/my/plans/{plan_id}/edit", data={"name": " "}, follow_redirects=True)
    assert b"Collection name is required" in collection_response.data
    assert b"Meal plan name is required" in plan_response.data
