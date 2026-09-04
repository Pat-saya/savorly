import os

from dotenv import load_dotenv
from flask import Flask, render_template

from .extensions import csrf, db, migrate


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg://localhost/mealmate")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
        MEALDB_API_KEY=os.getenv("MEALDB_API_KEY", "1"),
        MEALDB_BASE_URL=os.getenv("MEALDB_BASE_URL", "https://www.themealdb.com/api/json/v1"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from .auth import bp as auth_bp
    from .main import bp as main_bp
    from .user_data import bp as user_data_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(user_data_bp)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, title="That page is private", message="You do not have permission to access this resource."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, title="We couldn't find that", message="The page or recipe may have moved."), 404

    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("error.html", code=400, title="That request didn't work", message="Please return to the page and try again."), 400

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("error.html", code=500, title="Something went wrong", message="Please try again in a moment."), 500

    return app
