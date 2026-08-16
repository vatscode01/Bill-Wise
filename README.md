# BillWise

> **Personal bill & subscription tracker** — built over an 8-week roadmap.
> Track bills, manage subscriptions, extract invoice data with AI, and get email reminders before things go overdue.

---

## Features

| Feature | Details |
|---|---|
| **Authentication** | JWT-based register/login; passwords hashed with bcrypt |
| **Bill Management** | Full CRUD — create, list, update, mark-paid, delete |
| **Subscriptions** | Monthly/yearly subscriptions with active/cancelled toggle |
| **AI Extraction** | Upload a PDF or image → GPT-4o-mini pulls out provider, amount, due date automatically |
| **Dashboard Stats** | Upcoming, overdue, paid-this-month, recurring-monthly stat cards |
| **Spending Charts** | 6-month paid-bill bar chart + top-5 providers breakdown |
| **Email Reminders** | APScheduler cron fires at 8 AM daily; sends reminders N days before due date |
| **Dockerized** | One `docker compose up` for local dev; `docker-compose.prod.yml` overrides for production |
| **Nginx (prod)** | Reverse proxy with HTTPS, security headers, and large-upload support for AI extraction |

---

## Tech Stack

**Backend** — FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL · python-jose · passlib · OpenAI SDK · fastapi-mail · APScheduler  
**Frontend** — Next.js 14 (App Router) · React 18 · Tailwind CSS  
**Infra** — Docker Compose · Nginx

---

## Quick Start (Local Dev)

### 1. Clone & configure

```bash
# copy the env example and fill in your values
cp backend/.env.example backend/.env
```

At minimum, set your `JWT_SECRET`. For AI extraction, add your `OPENAI_API_KEY`. Email reminders need `MAIL_USERNAME` / `MAIL_PASSWORD`.

### 2. Start everything

```bash
docker compose up --build
```

This starts PostgreSQL, runs Alembic migrations, and boots the FastAPI backend (port 8000) and Next.js frontend (port 3000).

### 3. Open the app

- **Frontend**: http://localhost:3000
- **API docs (Swagger)**: http://localhost:8000/docs
- **API docs (Redoc)**: http://localhost:8000/redoc

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Required |
|---|---|---|
| `DATABASE_URL` | `postgresql://billwise:billwise@localhost:5432/billwise` | ✅ |
| `JWT_SECRET` | `dev-secret-change-me` | ✅ (change in prod) |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRE_MINUTES` | `60` | |
| `OPENAI_API_KEY` | _(empty)_ | For AI extraction |
| `MAIL_USERNAME` | _(empty)_ | For email reminders |
| `MAIL_PASSWORD` | _(empty)_ | For email reminders |
| `MAIL_FROM` | `noreply@billwise.app` | |
| `MAIL_SERVER` | `smtp.gmail.com` | |
| `MAIL_PORT` | `587` | |
| `REMINDER_DAYS_BEFORE` | `3` | `0` disables reminders |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list for prod |

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | ❌ | Create a new account |
| `POST` | `/auth/login` | ❌ | Get a JWT token |
| `GET` | `/bills` | ✅ | List your bills (optional `?status=` filter) |
| `POST` | `/bills` | ✅ | Create a bill |
| `GET` | `/bills/{id}` | ✅ | Get one bill |
| `PUT` | `/bills/{id}` | ✅ | Update a bill |
| `DELETE` | `/bills/{id}` | ✅ | Delete a bill |
| `POST` | `/bills/{id}/mark-paid` | ✅ | Mark a bill as paid |
| `POST` | `/bills/extract` | ✅ | AI extraction from PDF/image |
| `GET` | `/subscriptions` | ✅ | List your subscriptions |
| `POST` | `/subscriptions` | ✅ | Create a subscription |
| `PUT` | `/subscriptions/{id}` | ✅ | Update / cancel a subscription |
| `DELETE` | `/subscriptions/{id}` | ✅ | Delete a subscription |
| `GET` | `/dashboard/stats` | ✅ | Stat cards (upcoming, overdue, etc.) |
| `GET` | `/dashboard/charts` | ✅ | Monthly spending + provider breakdown |
| `GET` | `/health` | ❌ | Liveness probe |

---

## Running Tests

```bash
# From the backend directory (with a live test DB or using the conftest.py in-memory setup)
cd backend
pytest
```

Tests cover: auth, bill CRUD + ownership isolation, dashboard, AI extraction, email reminders, subscriptions.

---

## Production Deployment

```bash
# 1. Set all secrets in your shell or a secrets manager
# 2. Bring up with the prod overlay (adds Nginx, removes exposed ports)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

- Edit `nginx/nginx.prod.conf` → replace `YOUR_DOMAIN` with your domain.
- Place SSL certificates at `nginx/certs/fullchain.pem` and `nginx/certs/privkey.pem`.
- Set `CORS_ORIGINS=https://yourdomain.com` in your prod environment.

---

## Project Structure

```
BillWise Final/
├── backend/
│   ├── app/
│   │   ├── core/          # config, security (JWT/bcrypt), AI, email, scheduler
│   │   ├── models/        # SQLAlchemy ORM: User, Bill, Subscription
│   │   ├── routers/       # FastAPI routers: auth, bills, subscriptions, dashboard
│   │   ├── schemas/       # Pydantic schemas for request/response validation
│   │   ├── database.py    # SQLAlchemy engine + session factory
│   │   ├── deps.py        # get_current_user dependency
│   │   └── main.py        # App entry point, CORS, lifespan
│   ├── alembic/           # Database migrations
│   ├── tests/             # pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── app/               # Next.js App Router pages
│   ├── components/        # Navbar, ProtectedRoute, BillFormModal, etc.
│   ├── lib/               # api.ts, auth-context.tsx, format.ts
│   └── package.json
├── nginx/
│   └── nginx.prod.conf    # Production Nginx reverse-proxy config
├── docker-compose.yml          # Local dev
├── docker-compose.prod.yml     # Production overrides
└── .env.prod                   # Template for prod secrets (do NOT commit real values)
```

---

## Design Decisions

- **`Numeric` not `float` for money** — floats lose precision; `Decimal`/`Numeric(12,2)` prevents silent rounding errors.
- **404 not 403 for other users' resources** — a 403 confirms the resource exists; 404 doesn't leak that.
- **Overdue is a derived state** — computed at query time from `status=unpaid AND due_date < today`; the DB never needs a job to flip it.
- **Single-currency assumption** — v1 picks the user's most common bill currency as their "primary" for dashboard math. Multi-currency conversion is documented as a future improvement.
- **Inline HTML email templates** — avoids a `templates/` directory dependency; Jinja2 templates are the right next step for a production mailer.
