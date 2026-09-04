import pytest
from mealmate import create_app
from mealmate.extensions import db
from mealmate.models import User

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
        db.session.remove()
        db.engine.dispose()

@pytest.fixture
def client(app): return app.test_client()

@pytest.fixture
def user(app):
    with app.app_context():
        user = User(username="chef", email="chef@example.com")
        user.set_password("password1")
        db.session.add(user); db.session.commit()
        return user.id

@pytest.fixture
def login(client, user):
    client.post("/auth/login", data={"identity": "chef", "password": "password1"})
    return client
