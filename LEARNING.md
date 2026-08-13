# LEARNING.md

## Day 15 — Bill model
### What I learned
- Money should use a `Numeric`/`Decimal` column, never `float` — floats lose precision
  and can silently corrupt amounts after enough arithmetic.
- `status` and `billing_period` are modeled as Postgres enums so the database itself
  rejects invalid values, not just the API layer.
### What I built
- `Bill` SQLAlchemy model (`user_id`, `provider`, `amount`, `currency`, `due_date`,
  `billing_period`, `status`, `notes`, timestamps)
- Alembic migration `0001_initial_schema` for `users` + `bills`
### What confused me
- Whether to enforce currency as a fixed-length `String(3)` (ISO 4217 code) vs free text
  — went with fixed-length and uppercase-normalize in the schema layer.
### Tomorrow
- Build `POST /bills`.

## Day 16 — Create Bill API
### What I built
- `POST /bills`, scoped to the authenticated user via `get_current_user`
- Pydantic validation: `amount` must be `> 0` (`Field(gt=0)`), currency normalized to
  uppercase automatically
### What I fixed
- Initially let the client set `status` on create — closed that off; new bills always
  start `unpaid` server-side.

## Day 17 — Read bills
### What I learned
- `GET /bills` must always be implicitly scoped to `Bill.user_id == current_user.id`.
  There's no "give me every bill" endpoint at all — it's not a permission you disable,
  it's a query that was never written.
### What I built
- `GET /bills` (with optional `?status=` filter) and `GET /bills/{id}`

## Day 18 — Update & delete
### What I built
- `PUT /bills/{id}`, `DELETE /bills/{id}`
- A shared `_get_owned_bill_or_404` helper used by GET/PUT/DELETE so the ownership check
  can't accidentally be skipped in one of the three
### What I fixed
- Returning **404** instead of 403 for another user's bill — a 403 confirms the bill
  exists; 404 doesn't leak that.

## Day 19 — Real Bills page
### What I built
- `/bills` page fetching live data from FastAPI, replacing any placeholder rows

## Day 20 — Add/Edit forms
### What I built
- Add/Edit modal (`BillFormModal`) with client-side validation (required provider,
  amount > 0, required due date) as a first line of defense before the API's own checks
- Mark-as-paid action

## Day 21 — UX pass
### What I built
- Loading skeletons, an error state with a retry button, empty states (different copy
  for "no bills at all" vs "no bills matching this filter"), a delete confirmation
  dialog, and status filter tabs (All / Unpaid / Paid)
### What confused me
- Where "overdue" should live — decided it's a *derived* display state (today > due_date
  && still unpaid), not a value the backend has to actively flip, since that would need
  a scheduled job. Backend `status` stays `unpaid`/`paid`; the frontend/dashboard layer
  computes "overdue" for display.
### Tomorrow (Week 4)
- Dashboard stats and subscriptions.

## Week 3 — What I fixed / caught along the way
- Ownership isolation was the thing most worth testing directly rather than trusting by
  inspection: wrote tests where User B tries to GET/PUT/DELETE User A's bill and
  confirmed all three come back 404 and leave the bill untouched.
- Negative/zero amounts are rejected at the schema level (`Decimal, gt=0`), so a bad
  request never reaches the database.

## Day 22 — Dashboard design
### What I built
- Sketched four stat cards (Upcoming, Overdue, Paid This Month, Recurring) plus an
  "Upcoming Payments" list underneath, matching the roadmap's mock.
### What confused me
- Whether "Overdue" needed its own backend status. Decided no — same call as Day 21:
  it's `unpaid` + `due_date < today`, computed at query time, not a stored value.

## Day 23 — Dashboard stats backend
### What I built
- `GET /dashboard/stats`: upcoming / overdue / paid-this-month totals via SQLAlchemy
  `func.sum` + `func.count`, scoped to the authenticated user.
- `recurring_monthly` walks active subscriptions and normalizes yearly ones to a
  monthly-equivalent (`amount / 12`) so they can be added to monthly ones meaningfully.
### What I fixed
- First pass summed `Bill.amount` directly with Python `sum()` after fetching all rows.
  Switched to `func.sum` in the query so the database does the aggregation instead of
  pulling every row into memory — better practice once bill counts grow.

## Day 24 — Connect stats to frontend
### What I built
- Dashboard page now calls `/dashboard/stats` + `/dashboard/charts` on load; nothing is
  hardcoded.
### What I tested
- Added a bill → upcoming count went from 0 to 1. Marked it paid → upcoming count went
  back to 0 and paid-this-month picked it up. Wrote this as an actual test
  (`test_dashboard_updates_after_adding_and_paying_a_bill`) instead of just eyeballing it
  in the browser, since "no hardcoded numbers" is easy to silently break later.

## Day 25 — Spending charts
### What I built
- `GET /dashboard/charts`: last-6-months paid-bill totals (bucketed by
  `extract(year/month, due_date)`) and top-5 spending-by-provider.
- Rendered both as plain CSS bar charts (divs sized by percentage) instead of pulling in
  a charting library — the roadmap explicitly says "don't turn this into an analytics
  platform," and two small bar charts don't need one.
### What confused me
- Months with zero paid bills would just be missing from a raw SQL group-by. Built the
  6 month labels first, then filled in totals from the query results, so empty months
  still render as a zero-height bar instead of disappearing from the x-axis.

## Day 26 — Subscription model
### What I built
- `Subscription` model: name, provider, amount, currency, `billing_cycle`
  (monthly/yearly only — kept simple per the roadmap), `next_renewal`, `status`
  (active/cancelled).
- Added `updated_at` even though the roadmap's field list didn't list it, for the same
  reason `Bill` has one — PUT should be able to show when something last changed.

## Day 27 — Subscription CRUD + frontend
### What I built
- `POST/GET/PUT/DELETE /subscriptions`, reusing the exact same ownership-check pattern
  (`_get_owned_subscription_or_404`) as bills — 404, not 403, for someone else's
  subscription.
- `/subscriptions` page: list, add/edit modal, delete confirmation, active/cancelled
  filter tabs, cancel/reactivate toggle instead of delete-as-the-only-option (a
  cancelled sub can still be looked back on).

## Day 28 — Recurring monthly spend
### What I built
- Displayed on the Subscriptions page: sum of active subscriptions, yearly ones divided
  by 12, same normalization logic as the backend's `recurring_monthly` stat (computed
  client-side here since it only needs the already-loaded list, but the math has to
  match the backend exactly or the two numbers on Dashboard vs Subscriptions would
  disagree).

## Week 4 — What I fixed / caught along the way
- Multi-currency bills would make "sum everything" meaningless (₹500 + $500 ≠ 1000 of
  anything). For v1, picked the user's most common bill currency as their "primary"
  currency and assumed a single-currency user, same as most personal-finance apps do
  before they add real conversion. Documented this as a Future Improvement rather than
  quietly ignoring it.
- Interview question I should be ready for: "why does recurring_monthly count active
  subscriptions but paid_this_month counts bills regardless of currency mixing?" —
  because bills already share one derived "primary currency" for the whole stats
  response, so every card on the dashboard is internally consistent even though it's an
  approximation for a genuinely multi-currency user.

### Tomorrow (Week 5)
- AI bill extraction: OpenAI API basics, structured extraction, validating AI output
  before it touches the database.

