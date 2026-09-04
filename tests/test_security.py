from mealmate import create_app
from mealmate.extensions import db


def test_csrf_rejects_post_without_token():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SECRET_KEY": "csrf-test",
        "WTF_CSRF_ENABLED": True,
    })
    with app.app_context():
        db.create_all()
        response = app.test_client().post("/auth/register", data={
            "username": "chef", "email": "chef@example.com", "password": "password1"
        })
        assert response.status_code == 400
        assert b"That request didn&#39;t work" in response.data
        db.drop_all()
        db.session.remove()
        db.engine.dispose()
