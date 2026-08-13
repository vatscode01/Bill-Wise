VALID_BILL = {
    "provider": "Electricity",
    "amount": "2431.00",
    "currency": "inr",
    "due_date": "2026-08-18",
    "billing_period": "monthly",
}


def test_create_bill(client, auth_headers):
    headers = auth_headers()
    r = client.post("/bills", json=VALID_BILL, headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert body["provider"] == "Electricity"
    assert body["currency"] == "INR"  # normalized to uppercase
    assert body["status"] == "unpaid"


def test_create_bill_requires_auth(client):
    r = client.post("/bills", json=VALID_BILL)
    assert r.status_code == 401


def test_create_bill_rejects_negative_amount(client, auth_headers):
    headers = auth_headers()
    payload = {**VALID_BILL, "amount": "-10"}
    r = client.post("/bills", json=payload, headers=headers)
    assert r.status_code == 422


def test_list_bills_only_returns_own_bills(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    client.post("/bills", json=VALID_BILL, headers=headers_a)

    r = client.get("/bills", headers=headers_a)
    assert len(r.json()) == 1

    r = client.get("/bills", headers=headers_b)
    assert len(r.json()) == 0


def test_get_single_bill(client, auth_headers):
    headers = auth_headers()
    created = client.post("/bills", json=VALID_BILL, headers=headers).json()
    r = client.get(f"/bills/{created['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_nonexistent_bill_returns_404(client, auth_headers):
    headers = auth_headers()
    r = client.get("/bills/00000000-0000-0000-0000-000000000000", headers=headers)
    assert r.status_code == 404


def test_user_cannot_read_another_users_bill(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    bill = client.post("/bills", json=VALID_BILL, headers=headers_a).json()

    r = client.get(f"/bills/{bill['id']}", headers=headers_b)
    assert r.status_code == 404


def test_user_cannot_update_another_users_bill(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    bill = client.post("/bills", json=VALID_BILL, headers=headers_a).json()

    r = client.put(f"/bills/{bill['id']}", json={"provider": "Hacked"}, headers=headers_b)
    assert r.status_code == 404

    # confirm it really wasn't changed
    r = client.get(f"/bills/{bill['id']}", headers=headers_a)
    assert r.json()["provider"] == "Electricity"


def test_user_cannot_delete_another_users_bill(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    bill = client.post("/bills", json=VALID_BILL, headers=headers_a).json()

    r = client.delete(f"/bills/{bill['id']}", headers=headers_b)
    assert r.status_code == 404

    r = client.get(f"/bills/{bill['id']}", headers=headers_a)
    assert r.status_code == 200


def test_update_own_bill(client, auth_headers):
    headers = auth_headers()
    bill = client.post("/bills", json=VALID_BILL, headers=headers).json()
    r = client.put(f"/bills/{bill['id']}", json={"amount": "500.00"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["amount"] == "500.00"


def test_delete_own_bill(client, auth_headers):
    headers = auth_headers()
    bill = client.post("/bills", json=VALID_BILL, headers=headers).json()
    r = client.delete(f"/bills/{bill['id']}", headers=headers)
    assert r.status_code == 204
    r = client.get(f"/bills/{bill['id']}", headers=headers)
    assert r.status_code == 404


def test_mark_bill_paid(client, auth_headers):
    headers = auth_headers()
    bill = client.post("/bills", json=VALID_BILL, headers=headers).json()
    r = client.post(f"/bills/{bill['id']}/mark-paid", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "paid"


def test_filter_bills_by_status(client, auth_headers):
    headers = auth_headers()
    b1 = client.post("/bills", json=VALID_BILL, headers=headers).json()
    client.post("/bills", json={**VALID_BILL, "provider": "Internet"}, headers=headers)
    client.post(f"/bills/{b1['id']}/mark-paid", headers=headers)

    r = client.get("/bills?status=paid", headers=headers)
    assert len(r.json()) == 1
    assert r.json()[0]["provider"] == "Electricity"

    r = client.get("/bills?status=unpaid", headers=headers)
    assert len(r.json()) == 1
    assert r.json()[0]["provider"] == "Internet"
