# Pawbnb – Dog Care Marketplace

Airbnb-style platform for dog sitting, walking and daycare. Inspired by Rover.

## Features

- **Two roles**: Pet Owners & Sitters
- **Services**: Boarding, Walking, Daycare
- **Request → Accept flow**
  - Owner selects dates & authorizes payment (hold)
  - Sitter must Accept (payment is captured) or Decline (hold released / refunded)
- **Calendar blocking**: already booked dates cannot be selected
- **Map search** with sitters across Europe
- **Messaging** per booking
- **Ratings & reviews**
- **Stripe** ready (manual capture) + demo mode

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

### Optional Stripe

```bash
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Demo accounts

| Role   | Email              | Password |
|--------|--------------------|----------|
| Sitter | maria@example.com  | demo123  |
| Owner  | owner@example.com  | demo123  |

(Other sitters also use password `demo123`)

## Booking flow

1. Owner searches → opens sitter → requests dates
2. Owner authorizes payment (card is held, not yet charged)
3. Sitter sees the request and can **Accept** or **Decline**
4. Accept → payment captured  
   Decline → authorization cancelled / refunded
5. After the stay both parties can mark completed and the owner leaves a review
