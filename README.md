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
