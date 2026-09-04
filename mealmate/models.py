from datetime import date, datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


collection_recipes = db.Table(
    "collection_recipes",
    db.Column("collection_id", db.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    db.Column("saved_recipe_id", db.ForeignKey("saved_recipes.id", ondelete="CASCADE"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    saved_recipes = db.relationship("SavedRecipe", back_populates="user", cascade="all, delete-orphan")
    collections = db.relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    meal_plans = db.relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SavedRecipe(db.Model):
    __tablename__ = "saved_recipes"
    __table_args__ = (db.UniqueConstraint("user_id", "external_id", name="uq_user_recipe"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.Text)
    category = db.Column(db.String(100))
    cuisine = db.Column(db.String(100))
    note = db.Column(db.Text, nullable=False, default="")
    saved_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="saved_recipes")
    collections = db.relationship("Collection", secondary=collection_recipes, back_populates="recipes")
    meal_plan_items = db.relationship("MealPlanItem", back_populates="recipe", cascade="all, delete-orphan")


class Collection(db.Model):
    __tablename__ = "collections"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_user_collection_name"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)

    user = db.relationship("User", back_populates="collections")
    recipes = db.relationship("SavedRecipe", secondary=collection_recipes, back_populates="collections")


class MealPlan(db.Model):
    __tablename__ = "meal_plans"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)

    user = db.relationship("User", back_populates="meal_plans")
    items = db.relationship("MealPlanItem", back_populates="plan", cascade="all, delete-orphan", order_by="MealPlanItem.planned_for")


class MealPlanItem(db.Model):
    __tablename__ = "meal_plan_items"
    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    saved_recipe_id = db.Column(db.Integer, db.ForeignKey("saved_recipes.id", ondelete="CASCADE"), nullable=False)
    planned_for = db.Column(db.Date, nullable=False, default=date.today)
    meal_type = db.Column(db.String(20), nullable=False, default="Dinner")

    plan = db.relationship("MealPlan", back_populates="items")
    recipe = db.relationship("SavedRecipe", back_populates="meal_plan_items")

