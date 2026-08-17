"""Stripe PaymentIntent helpers (manual capture) + webhook handling."""
from __future__ import annotations

import logging
from flask import current_app

logger = logging.getLogger(__name__)

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None  # type: ignore


def is_configured() -> bool:
    return STRIPE_AVAILABLE and bool(current_app.config.get('STRIPE_SECRET_KEY'))


def _api():
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    return stripe


def create_payment_intent(booking) -> dict:
    """Create a PaymentIntent with manual capture. Returns client_secret + id."""
    api = _api()
    amount_cents = max(int(round(float(booking.total_price) * 100)), 50)  # Stripe min
    intent = api.PaymentIntent.create(
        amount=amount_cents,
        currency=current_app.config.get('STRIPE_CURRENCY', 'eur'),
        capture_method='manual',
        automatic_payment_methods={'enabled': True},
        metadata={
            'booking_id': str(booking.id),
            'owner_id': str(booking.owner_id),
            'sitter_id': str(booking.sitter_id),
        },
        description=f'Pawbnb {booking.service_type} – {booking.dog_name or "pet"}',
    )
    return {'id': intent.id, 'client_secret': intent.client_secret, 'status': intent.status}


def capture_payment_intent(payment_intent_id: str) -> bool:
    api = _api()
    intent = api.PaymentIntent.capture(payment_intent_id)
    return intent.status == 'succeeded'


def cancel_or_refund(payment_intent_id: str) -> str:
    """Cancel uncaptured intent or refund if already succeeded. Returns new status label."""
    api = _api()
    intent = api.PaymentIntent.retrieve(payment_intent_id)
    if intent.status == 'requires_capture':
        api.PaymentIntent.cancel(payment_intent_id)
        return 'cancelled'
    if intent.status == 'succeeded':
        api.Refund.create(payment_intent=payment_intent_id)
        return 'refunded'
    if intent.status in ('canceled', 'cancelled'):
        return 'cancelled'
    logger.warning('Unexpected PI status %s for %s', intent.status, payment_intent_id)
    return intent.status


def construct_webhook_event(payload: bytes, sig_header: str):
    api = _api()
    secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    if not secret:
        raise ValueError('STRIPE_WEBHOOK_SECRET not configured')
    return api.Webhook.construct_event(payload, sig_header, secret)
