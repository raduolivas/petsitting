# Pawbnb – Professional Dog Care Marketplace

Airbnb-style platform for dog sitting, walking and daycare.

## Stack

- **Flask** application factory + blueprints
- **SQLAlchemy** + **Flask-Migrate** (Alembic)
- **PostgreSQL** in production (SQLite for local dev)
- **Flask-Login** + **Flask-WTF** (CSRF)
- **Flask-Talisman** security headers
- **Stripe** (manual capture authorize → accept/refund)
- **Gunicorn** + **Docker** / docker-compose

## Quick start (local)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit SECRET_KEY if you want

export FLASK_APP=wsgi:app
export FLASK_ENV=development

flask db init        # first time only
flask db migrate -m "initial"
flask db upgrade
flask seed

python run.py
```

Open http://127.0.0.1:5000

### Demo accounts

| Role   | Email             | Password |
|--------|-------------------|----------|
| Sitter | maria@example.com | demo123  |
| Owner  | owner@example.com | demo123  |

## Production (Docker)

```bash
cp .env.example .env
# set SECRET_KEY and optionally Stripe keys

docker compose up --build
```

App: http://localhost:8000  
Health: http://localhost:8000/api/health

## Project layout

```
app/
  __init__.py          # create_app factory
  config.py            # Dev / Prod / Test configs
  extensions.py        # db, login, migrate, csrf
  models.py
  seed.py
  services/            # business logic
  blueprints/
    auth/
    main/
    sitters/
    bookings/
    api/
  templates/
  static/
wsgi.py                # production entry
run.py                 # development entry
Dockerfile
docker-compose.yml
migrations/            # Alembic (after flask db init)
```

## Booking flow

1. Owner requests dates → authorizes payment (hold)
2. Sitter **Accepts** → payment captured  
   or **Declines** → hold released / refunded
3. Stay completed → review

## Environment variables

See `.env.example`. Required in production:

- `SECRET_KEY`
- `DATABASE_URL` (PostgreSQL)
- `FLASK_ENV=production`


## Tests & CI

```bash
pip install -r requirements.txt
FLASK_ENV=testing SECRET_KEY=test pytest
# or
make test
```

GitHub Actions runs tests on push/PR to `main` (Python 3.11 and 3.12).

## Makefile shortcuts

```bash
make install   # venv + deps
make migrate
make seed
make run
make test
make docker-up
```


## Payments (Stripe)

1. Set `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` (test mode is fine).
2. For webhooks locally: `stripe listen --forward-to localhost:5000/webhooks/stripe` and set `STRIPE_WEBHOOK_SECRET`.
3. Payment Element authorizes the card (`capture_method=manual`).
4. Sitter **Accept** → capture · **Decline** → cancel/refund.

Without Stripe keys, the demo "Authorize" button still works.

## Email

Configure SMTP via `MAIL_*` env vars. With empty `MAIL_SERVER` (or `MAIL_SUPPRESS_SEND=1`), emails are printed to the console.

## Image uploads

Sitters can upload a profile photo on **Edit profile**. Files are stored under `app/static/uploads/sitters/`.

## Redis rate limits

```bash
# docker compose includes Redis
RATELIMIT_STORAGE_URI=redis://localhost:6379/0
```

In development the default is in-memory storage.
