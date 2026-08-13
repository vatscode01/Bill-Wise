VALID_SUB = {
    "name": "Netflix",
    "provider": "Netflix",
    "amount": "649.00",
    "currency": "inr",
    "billing_cycle": "monthly",
    "next_renewal": "2026-08-20",
}


def test_create_subscription(client, auth_headers):
    headers = auth_headers()
    r = client.post("/subscriptions", json=VALID_SUB, headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Netflix"
    assert body["currency"] == "INR"  # normalized to uppercase
    assert body["status"] == "active"


def test_create_subscription_requires_auth(client):
    r = client.post("/subscriptions", json=VALID_SUB)
    assert r.status_code == 401


def test_create_subscription_rejects_negative_amount(client, auth_headers):
    headers = auth_headers()
    payload = {**VALID_SUB, "amount": "-10"}
    r = client.post("/subscriptions", json=payload, headers=headers)
    assert r.status_code == 422


def test_list_subscriptions_only_returns_own(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    client.post("/subscriptions", json=VALID_SUB, headers=headers_a)

    r = client.get("/subscriptions", headers=headers_a)
    assert len(r.json()) == 1

    r = client.get("/subscriptions", headers=headers_b)
    assert len(r.json()) == 0


def test_user_cannot_read_another_users_subscription(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    sub = client.post("/subscriptions", json=VALID_SUB, headers=headers_a).json()

    r = client.get(f"/subscriptions/{sub['id']}", headers=headers_b)
    assert r.status_code == 404


def test_user_cannot_update_another_users_subscription(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    sub = client.post("/subscriptions", json=VALID_SUB, headers=headers_a).json()

    r = client.put(f"/subscriptions/{sub['id']}", json={"name": "Hacked"}, headers=headers_b)
    assert r.status_code == 404

    r = client.get(f"/subscriptions/{sub['id']}", headers=headers_a)
    assert r.json()["name"] == "Netflix"


def test_user_cannot_delete_another_users_subscription(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    sub = client.post("/subscriptions", json=VALID_SUB, headers=headers_a).json()

    r = client.delete(f"/subscriptions/{sub['id']}", headers=headers_b)
    assert r.status_code == 404


def test_update_own_subscription(client, auth_headers):
    headers = auth_headers()
    sub = client.post("/subscriptions", json=VALID_SUB, headers=headers).json()
    r = client.put(f"/subscriptions/{sub['id']}", json={"status": "cancelled"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_delete_own_subscription(client, auth_headers):
    headers = auth_headers()
    sub = client.post("/subscriptions", json=VALID_SUB, headers=headers).json()
    r = client.delete(f"/subscriptions/{sub['id']}", headers=headers)
    assert r.status_code == 204
    r = client.get(f"/subscriptions/{sub['id']}", headers=headers)
    assert r.status_code == 404


def test_filter_subscriptions_by_status(client, auth_headers):
    headers = auth_headers()
    s1 = client.post("/subscriptions", json=VALID_SUB, headers=headers).json()
    client.post("/subscriptions", json={**VALID_SUB, "name": "Spotify"}, headers=headers)
    client.put(f"/subscriptions/{s1['id']}", json={"status": "cancelled"}, headers=headers)

    r = client.get("/subscriptions?status_filter=cancelled", headers=headers)
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Netflix"

    r = client.get("/subscriptions?status_filter=active", headers=headers)
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Spotify"
