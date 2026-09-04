from mealmate.extensions import db
from mealmate.models import User

def test_register_hashes_password_and_logs_in(app, client):
    response = client.post("/auth/register", data={"username": "newchef", "email": "new@example.com", "password": "secret123"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome to Savorly" in response.data
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == "newchef"))
        assert user.password_hash != "secret123"
        assert user.check_password("secret123")

def test_bad_login_is_rejected(client, user):
    response = client.post("/auth/login", data={"identity": "chef", "password": "wrong"})
    assert b"Incorrect username/email or password" in response.data

def test_protected_page_redirects(client):
    response = client.get("/my/saved")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_duplicate_registration_is_rejected(client, user):
    response = client.post("/auth/register", data={
        "username": "chef", "email": "different@example.com", "password": "password1"
    })
    assert b"already registered" in response.data


def test_logout_clears_session(login):
    login.post("/auth/logout")
    assert login.get("/my/saved").status_code == 302
