from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .models import SavedRecipe
from .recipe_api import (
    RecipeAPIError,
    browse_area,
    browse_category,
    get_recipe,
    list_categories,
    search_recipes,
)
from .extensions import db

bp = Blueprint("main", __name__)


def recipes_return_to(candidate=None):
    """Allow returning only to the Discover/results list, never off-site or to detail URLs."""
    value = (candidate if candidate is not None else request.args.get("return_to", "")).strip()
    if value in {"/recipes", "/recipes?"} or value.startswith("/recipes?"):
        return value.rstrip("?") or "/recipes"
    return url_for("main.search")


@bp.get("/")
def home():
    return render_template("home.html")


@bp.get("/health")
def health():
    return {"status": "ok"}


@bp.get("/browse", strict_slashes=False)
def browse():
    preferred_categories = {"Vegetarian", "Vegan", "Seafood", "Chicken", "Pasta", "Dessert"}
    try:
        categories = [item for item in list_categories() if item in preferred_categories]
        error = None
    except RecipeAPIError as exc:
        categories, error = [], str(exc)
    return render_template("recipes/browse.html", categories=categories, error=error)


@bp.get("/recipes")
def search():
    query = request.args.get("q", "").strip()
    area = request.args.get("area", "").strip()
    category = request.args.get("category", "").strip()
    recipes, categories, error = [], [], None
    try:
        categories = list_categories()
        if category:
            recipes = browse_category(category)
            if query:
                joined_query = "".join(query.casefold().split())
                recipes = [recipe for recipe in recipes if joined_query in "".join(recipe.name.casefold().split())]
        elif area:
            recipes = browse_area(area)
            if query:
                joined_query = "".join(query.casefold().split())
                recipes = [recipe for recipe in recipes if joined_query in "".join(recipe.name.casefold().split())]
        elif query:
            recipes = search_recipes(query)
    except RecipeAPIError as exc:
        error = str(exc)
    saved_ids = set()
    if g.user:
        saved_ids = set(db.session.scalars(db.select(SavedRecipe.external_id).where(SavedRecipe.user_id == g.user.id)))
    return render_template("recipes/search.html", query=query, area=area, category=category,
                           categories=categories, recipes=recipes, saved_ids=saved_ids, error=error)


@bp.get("/recipes/<recipe_id>")
def recipe_detail(recipe_id):
    try:
        recipe = get_recipe(recipe_id)
    except RecipeAPIError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("main.search"))
    if recipe is None:
        abort(404)
    saved = None
    if g.user:
        saved = db.session.scalar(db.select(SavedRecipe).where(SavedRecipe.user_id == g.user.id, SavedRecipe.external_id == recipe_id))
    return render_template(
        "recipes/detail.html",
        recipe=recipe,
        saved=saved,
        back_to_recipes=recipes_return_to(),
    )
