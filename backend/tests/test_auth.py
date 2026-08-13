def test_register_creates_user(client):
    r = client.post("/auth/register", json={"email": "a@test.com", "password": "password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@test.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client):
    client.post("/auth/register", json={"email": "a@test.com", "password": "password123"})
    r = client.post("/auth/register", json={"email": "a@test.com", "password": "password123"})
    assert r.status_code == 400


def test_register_rejects_short_password(client):
    r = client.post("/auth/register", json={"email": "a@test.com", "password": "short"})
    assert r.status_code == 422


def test_login_succeeds_with_correct_credentials(client):
    client.post("/auth/register", json={"email": "a@test.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "a@test.com", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_rejects_wrong_password(client):
    client.post("/auth/register", json={"email": "a@test.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "a@test.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_rejects_unknown_email(client):
    r = client.post("/auth/login", json={"email": "ghost@test.com", "password": "password123"})
    assert r.status_code == 401


def test_protected_route_rejects_missing_token(client):
    r = client.get("/bills")
    assert r.status_code == 401


def test_protected_route_rejects_invalid_token(client):
    r = client.get("/bills", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
