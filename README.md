# Pawbnb – Dog Care Marketplace (MVP+)

Airbnb-style platform for dog sitting, walking and daycare.

## What's new in this version

1. **Stripe payments** (test mode ready)
   - Set `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` env vars to enable real Checkout
   - Demo/mock payment always available as fallback

2. **Improved map & more cities**
   - Sitters in Lisbon, Porto, Sintra, Faro, Madrid, Barcelona, Paris, Rome, Berlin
   - Country filter + map auto-fits to results

3. **Messaging system**
   - Chat between owner and sitter on every booking
   - Message count shown on dashboards

4. **Polish**
   - Better booking detail page
   - Cleaner cards, filters, empty states
   - Country field on sitter profiles

## Features

- Two roles: Pet Owner & Sitter
- Services: Boarding, Walking, Daycare
- Prices set by sitters
- Map with pins (Leaflet)
- Ratings & reviews
- Secure payment flow (Stripe or demo)

## Run

```bash
pip install flask flask-sqlalchemy flask-login stripe

# Optional: enable real Stripe test payments
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_PUBLISHABLE_KEY=pk_test_...

python app.py
```

Open http://127.0.0.1:5000

### Demo accounts

| Role   | Email              | Password |
|--------|--------------------|----------|
| Sitter | maria@example.com  | demo123  |
| Sitter | joao@example.com   | demo123  |
| Sitter | sofia@example.com  | demo123  |
| Owner  | owner@example.com  | demo123  |

(Other sitters: carlos, lucia, pierre, giulia, hans, ana.faro – all password `demo123`)

## Stripe test card

Use `4242 4242 4242 4242` with any future expiry and any CVC.
