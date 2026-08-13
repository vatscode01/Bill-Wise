from datetime import date, timedelta


def _bill(provider="Electricity", amount="1000.00", due_offset_days=5, currency="INR"):
    return {
        "provider": provider,
        "amount": amount,
        "currency": currency,
        "due_date": (date.today() + timedelta(days=due_offset_days)).isoformat(),
        "billing_period": "monthly",
    }


def test_stats_requires_auth(client):
    r = client.get("/dashboard/stats")
    assert r.status_code == 401


def test_stats_are_zero_for_new_user(client, auth_headers):
    headers = auth_headers()
    r = client.get("/dashboard/stats", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["upcoming"]["amount"] == "0"
    assert body["overdue"]["amount"] == "0"
    assert body["paid_this_month"]["amount"] == "0"
    assert body["recurring_monthly"]["amount"] == "0"
    assert body["upcoming_payments"] == []


def test_upcoming_and_overdue_are_split_correctly(client, auth_headers):
    headers = auth_headers()
    client.post("/bills", json=_bill(due_offset_days=5), headers=headers)  # upcoming
    client.post("/bills", json=_bill(provider="Internet", due_offset_days=-3), headers=headers)  # overdue

    r = client.get("/dashboard/stats", headers=headers)
    body = r.json()
    assert body["upcoming"]["amount"] == "1000.00"
    assert body["upcoming"]["count"] == 1
    assert body["overdue"]["amount"] == "1000.00"
    assert body["overdue"]["count"] == 1


def test_paid_this_month_reflects_marked_paid_bills(client, auth_headers):
    headers = auth_headers()
    bill = client.post("/bills", json=_bill(due_offset_days=0), headers=headers).json()
    client.post(f"/bills/{bill['id']}/mark-paid", headers=headers)

    r = client.get("/dashboard/stats", headers=headers)
    body = r.json()
    assert body["paid_this_month"]["amount"] == "1000.00"
    assert body["paid_this_month"]["count"] == 1


def test_dashboard_updates_after_adding_and_paying_a_bill(client, auth_headers):
    """No-hardcoded-numbers check (Day 24): stats must change as data changes."""
    headers = auth_headers()

    before = client.get("/dashboard/stats", headers=headers).json()
    assert before["upcoming"]["count"] == 0

    bill = client.post("/bills", json=_bill(due_offset_days=2), headers=headers).json()
    after_add = client.get("/dashboard/stats", headers=headers).json()
    assert after_add["upcoming"]["count"] == 1

    client.post(f"/bills/{bill['id']}/mark-paid", headers=headers)
    after_pay = client.get("/dashboard/stats", headers=headers).json()
    assert after_pay["upcoming"]["count"] == 0


def test_recurring_monthly_normalizes_yearly_subscriptions(client, auth_headers):
    headers = auth_headers()
    client.post(
        "/subscriptions",
        json={
            "name": "Netflix",
            "provider": "Netflix",
            "amount": "649.00",
            "currency": "INR",
            "billing_cycle": "monthly",
            "next_renewal": date.today().isoformat(),
        },
        headers=headers,
    )
    client.post(
        "/subscriptions",
        json={
            "name": "Cloud Backup",
            "provider": "CloudCo",
            "amount": "1200.00",
            "currency": "INR",
            "billing_cycle": "yearly",
            "next_renewal": date.today().isoformat(),
        },
        headers=headers,
    )

    r = client.get("/dashboard/stats", headers=headers)
    body = r.json()
    # 649 (monthly) + 1200/12=100 (yearly normalized) = 749
    assert body["recurring_monthly"]["amount"] == "749.00"
    assert body["recurring_monthly"]["count"] == 2


def test_cancelled_subscriptions_excluded_from_recurring_spend(client, auth_headers):
    headers = auth_headers()
    sub = client.post(
        "/subscriptions",
        json={
            "name": "Netflix",
            "provider": "Netflix",
            "amount": "649.00",
            "currency": "INR",
            "billing_cycle": "monthly",
            "next_renewal": date.today().isoformat(),
        },
        headers=headers,
    ).json()
    client.put(f"/subscriptions/{sub['id']}", json={"status": "cancelled"}, headers=headers)

    r = client.get("/dashboard/stats", headers=headers)
    assert r.json()["recurring_monthly"]["amount"] == "0"


def test_upcoming_payments_list_is_sorted_and_scoped(client, auth_headers):
    headers_a = auth_headers("a@test.com")
    headers_b = auth_headers("b@test.com")
    client.post("/bills", json=_bill(provider="Later", due_offset_days=10), headers=headers_a)
    client.post("/bills", json=_bill(provider="Sooner", due_offset_days=2), headers=headers_a)
    client.post("/bills", json=_bill(provider="NotMine", due_offset_days=1), headers=headers_b)

    r = client.get("/dashboard/stats", headers=headers_a)
    payments = r.json()["upcoming_payments"]
    assert [p["provider"] for p in payments] == ["Sooner", "Later"]


def test_charts_requires_auth(client):
    r = client.get("/dashboard/charts")
    assert r.status_code == 401


def test_charts_empty_state_for_new_user(client, auth_headers):
    headers = auth_headers()
    r = client.get("/dashboard/charts", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["monthly_spending"]) == 6
    assert all(point["amount"] == "0" for point in body["monthly_spending"])
    assert body["spending_by_provider"] == []


def test_charts_spending_by_provider(client, auth_headers):
    headers = auth_headers()
    b1 = client.post("/bills", json=_bill(provider="Electricity", amount="500.00"), headers=headers).json()
    b2 = client.post("/bills", json=_bill(provider="Internet", amount="900.00"), headers=headers).json()
    client.post(f"/bills/{b1['id']}/mark-paid", headers=headers)
    client.post(f"/bills/{b2['id']}/mark-paid", headers=headers)

    r = client.get("/dashboard/charts", headers=headers)
    providers = {row["provider"]: row["amount"] for row in r.json()["spending_by_provider"]}
    assert providers["Electricity"] == "500.00"
    assert providers["Internet"] == "900.00"
