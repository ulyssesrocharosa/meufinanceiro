from app.core.security import hash_password
from app.models.models import User, UserRole, Profile


def create_test_user(db, email="test@test.com", password="test123", role=UserRole.user):
    user = User(
        email=email,
        name="Test User",
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id))
    db.commit()
    return user


def test_login_success(client, db):
    create_test_user(db)
    r = client.post(
        "/auth/login",
        data={"email": "test@test.com", "password": "test123"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.headers["location"] == "/"


def test_login_wrong_password(client, db):
    create_test_user(db)
    r = client.post(
        "/auth/login",
        data={"email": "test@test.com", "password": "errado"},
        follow_redirects=False,
    )
    # On failure the login page is re-rendered with 400
    assert r.status_code in (200, 400)


def test_dashboard_requires_auth(client):
    r = client.get("/", follow_redirects=False)
    # Should redirect to /auth/login (302) because user is not authenticated
    assert r.status_code == 302


def test_logout(client, db):
    create_test_user(db)
    client.post(
        "/auth/login",
        data={"email": "test@test.com", "password": "test123"},
    )
    r = client.get("/auth/logout", follow_redirects=False)
    assert r.status_code == 302
