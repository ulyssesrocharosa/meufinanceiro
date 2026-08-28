from app.core.security import hash_password
from app.models.models import Account, AccountType, Category, CategoryType, Profile, User, UserRole


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
    r = client.post("/auth/logout", follow_redirects=False)
    assert r.status_code == 302


def test_transaction_rejects_foreign_category(client, db):
    user = create_test_user(db)
    other = create_test_user(db, email="other@test.com")
    account = Account(user_id=user.id, name="Conta", type=AccountType.checking, balance=0)
    category = Category(user_id=other.id, name="Privada", type=CategoryType.expense)
    db.add_all([account, category])
    db.commit()

    client.post("/auth/login", data={"email": user.email, "password": "test123"})
    response = client.post("/transactions", data={
        "account_id": account.id,
        "category_id": category.id,
        "amount": "10.00",
        "type": "expense",
        "transaction_date": "2026-08-28",
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "error=" in response.headers["location"]


def test_rejects_cross_origin_post(client):
    response = client.post("/auth/logout", headers={"Origin": "https://attacker.example"})
    assert response.status_code == 403


def test_accepts_same_origin_post(client):
    response = client.post("/auth/logout", headers={"Origin": "http://testserver"}, follow_redirects=False)
    assert response.status_code == 302
