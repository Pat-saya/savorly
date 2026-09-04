from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from .auth import login_required
from .extensions import db
from .models import Collection, MealPlan, MealPlanItem, SavedRecipe
from .recipe_api import RecipeAPIError, get_recipe

bp = Blueprint("user", __name__, url_prefix="/my")


def owned(model, item_id):
    item = db.session.get(model, item_id)
    if item is None:
        abort(404)
    if item.user_id != g.user.id:
        abort(403)
    return item


@bp.post("/saved/<recipe_id>")
@login_required
def save_recipe(recipe_id):
    existing = db.session.scalar(db.select(SavedRecipe).where(SavedRecipe.user_id == g.user.id, SavedRecipe.external_id == recipe_id))
    if existing:
        flash("Recipe is already saved.", "info")
    else:
        try:
            recipe = get_recipe(recipe_id)
        except RecipeAPIError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("main.recipe_detail", recipe_id=recipe_id))
        if recipe is None:
            abort(404)
        db.session.add(SavedRecipe(user_id=g.user.id, external_id=recipe.id, name=recipe.name,
                                   image_url=recipe.image_url, category=recipe.category, cuisine=recipe.cuisine))
        db.session.commit()
        flash("Recipe saved.", "success")
    return redirect(url_for("main.recipe_detail", recipe_id=recipe_id))


@bp.post("/saved/<int:saved_id>/delete")
@login_required
def unsave_recipe(saved_id):
    recipe = owned(SavedRecipe, saved_id)
    db.session.delete(recipe)
    db.session.commit()
    flash("Recipe removed from your saved recipes.", "success")
    return redirect(url_for("user.saved_recipes"))


@bp.route("/saved")
@login_required
def saved_recipes():
    query = request.args.get("q", "").strip()
    statement = db.select(SavedRecipe).where(SavedRecipe.user_id == g.user.id)
    if query:
        statement = statement.where(SavedRecipe.name.ilike(f"%{query}%"))
    recipes = db.session.scalars(statement.order_by(SavedRecipe.saved_at.desc())).all()
    return render_template("user/saved.html", recipes=recipes, query=query)


@bp.post("/saved/<int:saved_id>/note")
@login_required
def update_note(saved_id):
    recipe = owned(SavedRecipe, saved_id)
    recipe.note = request.form.get("note", "").strip()[:2000]
    db.session.commit()
    flash("Note updated.", "success")
    return redirect(url_for("main.recipe_detail", recipe_id=recipe.external_id))


@bp.route("/collections", methods=("GET", "POST"))
@login_required
def collections():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Collection name is required.", "danger")
        else:
            db.session.add(Collection(user_id=g.user.id, name=name[:80]))
            try:
                db.session.commit()
                flash("Collection created.", "success")
            except IntegrityError:
                db.session.rollback()
                flash("You already have a collection with that name.", "danger")
        return redirect(url_for("user.collections"))
    items = db.session.scalars(db.select(Collection).where(Collection.user_id == g.user.id).order_by(Collection.name)).all()
    return render_template("user/collections.html", collections=items)


@bp.get("/collections/<int:collection_id>")
@login_required
def collection_detail(collection_id):
    collection = owned(Collection, collection_id)
    saved = db.session.scalars(db.select(SavedRecipe).where(SavedRecipe.user_id == g.user.id).order_by(SavedRecipe.name)).all()
    return render_template("user/collection_detail.html", collection=collection, saved=saved)


@bp.post("/collections/<int:collection_id>/edit")
@login_required
def edit_collection(collection_id):
    collection = owned(Collection, collection_id)
    name = request.form.get("name", "").strip()
    if name:
        collection.name = name[:80]
        try:
            db.session.commit()
            flash("Collection renamed.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("That collection name is already in use.", "danger")
    else:
        flash("Collection name is required.", "danger")
    return redirect(url_for("user.collection_detail", collection_id=collection.id))


@bp.post("/collections/<int:collection_id>/delete")
@login_required
def delete_collection(collection_id):
    db.session.delete(owned(Collection, collection_id))
    db.session.commit()
    flash("Collection deleted. Your saved recipes were kept.", "success")
    return redirect(url_for("user.collections"))


@bp.post("/collections/<int:collection_id>/recipes")
@login_required
def add_to_collection(collection_id):
    collection = owned(Collection, collection_id)
    recipe = owned(SavedRecipe, request.form.get("saved_recipe_id", type=int))
    if recipe not in collection.recipes:
        collection.recipes.append(recipe)
        db.session.commit()
    flash("Recipe added to collection.", "success")
    return redirect(url_for("user.collection_detail", collection_id=collection.id))


@bp.post("/collections/<int:collection_id>/recipes/<int:saved_id>/delete")
@login_required
def remove_from_collection(collection_id, saved_id):
    collection, recipe = owned(Collection, collection_id), owned(SavedRecipe, saved_id)
    if recipe in collection.recipes:
        collection.recipes.remove(recipe)
        db.session.commit()
    flash("Recipe removed from collection.", "success")
    return redirect(url_for("user.collection_detail", collection_id=collection.id))


@bp.route("/plans", methods=("GET", "POST"))
@login_required
def meal_plans():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            db.session.add(MealPlan(user_id=g.user.id, name=name[:80]))
            db.session.commit()
            flash("Meal plan created.", "success")
        else:
            flash("Meal plan name is required.", "danger")
        return redirect(url_for("user.meal_plans"))
    plans = db.session.scalars(db.select(MealPlan).where(MealPlan.user_id == g.user.id).order_by(MealPlan.id.desc())).all()
    return render_template("user/plans.html", plans=plans)


@bp.get("/plans/<int:plan_id>")
@login_required
def meal_plan_detail(plan_id):
    plan = owned(MealPlan, plan_id)
    saved = db.session.scalars(db.select(SavedRecipe).where(SavedRecipe.user_id == g.user.id).order_by(SavedRecipe.name)).all()
    return render_template("user/plan_detail.html", plan=plan, saved=saved, today=date.today().isoformat())


@bp.post("/plans/<int:plan_id>/edit")
@login_required
def edit_meal_plan(plan_id):
    plan = owned(MealPlan, plan_id)
    name = request.form.get("name", "").strip()
    if name:
        plan.name = name[:80]
        db.session.commit()
        flash("Meal plan renamed.", "success")
    else:
        flash("Meal plan name is required.", "danger")
    return redirect(url_for("user.meal_plan_detail", plan_id=plan.id))


@bp.post("/plans/<int:plan_id>/delete")
@login_required
def delete_meal_plan(plan_id):
    db.session.delete(owned(MealPlan, plan_id))
    db.session.commit()
    flash("Meal plan deleted.", "success")
    return redirect(url_for("user.meal_plans"))


@bp.post("/plans/<int:plan_id>/items")
@login_required
def add_plan_item(plan_id):
    plan = owned(MealPlan, plan_id)
    recipe = owned(SavedRecipe, request.form.get("saved_recipe_id", type=int))
    try:
        planned_for = date.fromisoformat(request.form.get("planned_for", ""))
    except (TypeError, ValueError):
        flash("Choose a valid date.", "danger")
        return redirect(url_for("user.meal_plan_detail", plan_id=plan.id))
    meal_type = request.form.get("meal_type", "Dinner")
    if meal_type not in {"Breakfast", "Lunch", "Dinner", "Snack"}:
        meal_type = "Dinner"
    db.session.add(MealPlanItem(plan=plan, recipe=recipe, planned_for=planned_for, meal_type=meal_type))
    db.session.commit()
    flash("Meal added to plan.", "success")
    return redirect(url_for("user.meal_plan_detail", plan_id=plan.id))


@bp.post("/plans/<int:plan_id>/items/<int:item_id>/delete")
@login_required
def delete_plan_item(plan_id, item_id):
    plan = owned(MealPlan, plan_id)
    item = db.session.get(MealPlanItem, item_id)
    if item is None:
        abort(404)
    if item.plan != plan:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash("Meal removed from plan.", "success")
    return redirect(url_for("user.meal_plan_detail", plan_id=plan.id))
