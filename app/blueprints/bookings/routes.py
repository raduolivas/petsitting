from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.blueprints.bookings import bp
from app.extensions import db, csrf
from app.models import SitterProfile, Booking, Review, Message
from app.services.booking_service import (
    get_blocked_dates,
    dates_overlap,
    can_access_booking,
    recalculate_sitter_rating,
)
from app.services import email_service
from app.services import stripe_service


@bp.route('/book/<int:profile_id>', methods=['GET', 'POST'])
@login_required
def book(profile_id):
    if current_user.role != 'owner':
        flash('Only pet owners can make bookings.', 'error')
        return redirect(url_for('sitters.profile', profile_id=profile_id))

    profile = SitterProfile.query.get_or_404(profile_id)

    if request.method == 'POST':
        service_type = request.form.get('service_type')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        dog_name = request.form.get('dog_name', '')
        dog_breed = request.form.get('dog_breed', '')
        dog_size = request.form.get('dog_size', 'medium')
        notes = request.form.get('notes', '')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = (
                datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if end_date_str
                else start_date
            )
        except (ValueError, TypeError):
            flash('Invalid dates.', 'error')
            return redirect(url_for('bookings.book', profile_id=profile_id))

        existing = Booking.query.filter(
            Booking.sitter_id == profile.id,
            Booking.status.in_(['pending', 'confirmed']),
        ).all()
        for ex in existing:
            if dates_overlap(start_date, end_date, ex.start_date, ex.end_date):
                flash(
                    'Sorry, those dates are no longer available. Please choose different dates.',
                    'error',
                )
                return redirect(url_for('bookings.book', profile_id=profile_id))

        days = max((end_date - start_date).days + 1, 1)
        if service_type == 'boarding':
            total = profile.price_boarding_day * days
        elif service_type == 'daycare':
            total = profile.price_daycare_day * days
        elif service_type == 'walking':
            total = profile.price_walking_hour * days
        else:
            total = 0

        booking = Booking(
            owner_id=current_user.id,
            sitter_id=profile.id,
            service_type=service_type,
            start_date=start_date,
            end_date=end_date,
            dog_name=dog_name,
            dog_breed=dog_breed,
            dog_size=dog_size,
            notes=notes,
            total_price=total,
            status='pending',
            payment_status='unpaid',
        )
        db.session.add(booking)
        db.session.commit()

        flash('Booking request created. Please authorize payment.', 'success')
        return redirect(url_for('bookings.payment', booking_id=booking.id))

    blocked = get_blocked_dates(profile.id)
    return render_template('book.html', profile=profile, blocked_dates=blocked)


@bp.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.owner_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('main.dashboard'))

    if booking.payment_status in ('authorized', 'captured', 'paid'):
        flash('Payment already processed for this booking.', 'info')
        return redirect(url_for('bookings.detail', booking_id=booking.id))

    use_stripe = stripe_service.is_configured()
    client_secret = None

    # Demo / mock authorization
    if request.method == 'POST' and request.form.get('method') == 'mock':
        booking.payment_status = 'authorized'
        booking.status = 'pending'
        db.session.commit()
        try:
            email_service.notify_booking_requested(booking)
        except Exception:
            current_app.logger.exception('email notify failed')
        flash('Payment authorized (demo)! Waiting for the sitter to accept.', 'success')
        return redirect(url_for('bookings.detail', booking_id=booking.id))

    # Create PaymentIntent for Payment Element
    if use_stripe and not booking.stripe_payment_intent_id:
        try:
            result = stripe_service.create_payment_intent(booking)
            booking.stripe_payment_intent_id = result['id']
            db.session.commit()
            client_secret = result['client_secret']
        except Exception as e:
            current_app.logger.exception('Stripe PI create failed')
            flash(f'Could not start Stripe payment: {e}', 'error')
            use_stripe = False
    elif use_stripe and booking.stripe_payment_intent_id:
        # Re-fetch client secret if page reloaded
        try:
            import stripe
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            intent = stripe.PaymentIntent.retrieve(booking.stripe_payment_intent_id)
            client_secret = intent.client_secret
        except Exception:
            client_secret = None

    return render_template(
        'payment.html',
        booking=booking,
        use_stripe=use_stripe and bool(client_secret),
        client_secret=client_secret,
        stripe_pk=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''),
    )


@bp.route('/payment/<int:booking_id>/confirm', methods=['POST'])
@login_required
def payment_confirm(booking_id):
    """Called after Payment Element succeeds client-side."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.owner_id != current_user.id:
        abort(403)

    data = request.get_json(silent=True) or {}
    pi_id = data.get('payment_intent_id') or booking.stripe_payment_intent_id

    if pi_id:
        booking.stripe_payment_intent_id = pi_id
        booking.payment_status = 'authorized'
        booking.status = 'pending'
        db.session.commit()
        try:
            email_service.notify_booking_requested(booking)
        except Exception:
            current_app.logger.exception('email notify failed')
        return jsonify({'ok': True, 'redirect': url_for('bookings.detail', booking_id=booking.id)})

    return jsonify({'ok': False, 'error': 'missing payment_intent'}), 400


@bp.route('/webhooks/stripe', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    payload = request.get_data()
    sig = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe_service.construct_webhook_event(payload, sig)
    except Exception as e:
        current_app.logger.warning('Webhook signature error: %s', e)
        return jsonify({'error': str(e)}), 400

    etype = event['type']
    obj = event['data']['object']
    current_app.logger.info('Stripe webhook: %s', etype)

    if etype in ('payment_intent.amount_capturable_updated', 'payment_intent.succeeded'):
        pi_id = obj.get('id')
        booking = Booking.query.filter_by(stripe_payment_intent_id=pi_id).first()
        if booking:
            if etype == 'payment_intent.amount_capturable_updated' and booking.payment_status == 'unpaid':
                booking.payment_status = 'authorized'
                booking.status = 'pending'
                db.session.commit()
            elif etype == 'payment_intent.succeeded':
                booking.payment_status = 'captured'
                if booking.status == 'pending':
                    booking.status = 'confirmed'
                db.session.commit()

    elif etype == 'payment_intent.canceled':
        pi_id = obj.get('id')
        booking = Booking.query.filter_by(stripe_payment_intent_id=pi_id).first()
        if booking and booking.status == 'pending':
            booking.payment_status = 'refunded'
            booking.status = 'declined'
            db.session.commit()

    return jsonify({'received': True}), 200


@bp.route('/booking/<int:booking_id>')
@login_required
def detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not can_access_booking(booking, current_user):
        flash('Unauthorized.', 'error')
        return redirect(url_for('main.dashboard'))

    for msg in booking.messages:
        if msg.sender_id != current_user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return render_template('booking_detail.html', booking=booking)


@bp.route('/booking/<int:booking_id>/message', methods=['POST'])
@login_required
def send_message(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not can_access_booking(booking, current_user):
        flash('Unauthorized.', 'error')
        return redirect(url_for('main.dashboard'))

    content = request.form.get('content', '').strip()
    if not content:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))

    msg = Message(
        booking_id=booking.id,
        sender_id=current_user.id,
        content=content,
    )
    db.session.add(msg)
    db.session.commit()
    flash('Message sent!', 'success')
    return redirect(url_for('bookings.detail', booking_id=booking_id))


@bp.route('/booking/<int:booking_id>/accept', methods=['POST'])
@login_required
def accept(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    profile = current_user.sitter_profile
    if not profile or booking.sitter_id != profile.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('main.dashboard'))

    if booking.status != 'pending':
        flash('This booking is no longer pending.', 'info')
        return redirect(url_for('bookings.detail', booking_id=booking.id))

    if booking.stripe_payment_intent_id and stripe_service.is_configured():
        try:
            stripe_service.capture_payment_intent(booking.stripe_payment_intent_id)
            booking.payment_status = 'captured'
        except Exception as e:
            flash(f'Could not capture payment: {e}', 'error')
            return redirect(url_for('bookings.detail', booking_id=booking.id))
    else:
        booking.payment_status = 'captured'

    booking.status = 'confirmed'
    db.session.commit()
    try:
        email_service.notify_booking_accepted(booking)
    except Exception:
        current_app.logger.exception('email notify failed')
    flash('You accepted the booking. Payment has been captured.', 'success')
    return redirect(url_for('bookings.detail', booking_id=booking.id))


@bp.route('/booking/<int:booking_id>/decline', methods=['POST'])
@login_required
def decline(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    profile = current_user.sitter_profile
    if not profile or booking.sitter_id != profile.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('main.dashboard'))

    if booking.status != 'pending':
        flash('This booking is no longer pending.', 'info')
        return redirect(url_for('bookings.detail', booking_id=booking.id))

    if booking.stripe_payment_intent_id and stripe_service.is_configured():
        try:
            stripe_service.cancel_or_refund(booking.stripe_payment_intent_id)
            booking.payment_status = 'refunded'
        except Exception as e:
            flash(f'Refund/cancel issue: {e}. Marked as declined anyway.', 'error')
            booking.payment_status = 'refunded'
    else:
        booking.payment_status = 'refunded'

    booking.status = 'declined'
    db.session.commit()
    try:
        email_service.notify_booking_declined(booking)
    except Exception:
        current_app.logger.exception('email notify failed')
    flash('You declined the request. The payment authorization has been released.', 'info')
    return redirect(url_for('bookings.detail', booking_id=booking.id))


@bp.route('/booking/<int:booking_id>/complete', methods=['POST'])
@login_required
def complete(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not can_access_booking(booking, current_user):
        flash('Unauthorized.', 'error')
        return redirect(url_for('main.dashboard'))

    booking.status = 'completed'
    db.session.commit()
    flash('Booking marked as completed. You can now leave a review!', 'success')
    return redirect(url_for('bookings.detail', booking_id=booking_id))


@bp.route('/review/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def leave_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.owner_id != current_user.id:
        flash('Only the owner can leave a review.', 'error')
        return redirect(url_for('main.dashboard'))
    if booking.status != 'completed':
        flash('You can only review completed bookings.', 'error')
        return redirect(url_for('main.dashboard'))
    if booking.review:
        flash('You already reviewed this booking.', 'info')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        rating = max(1, min(5, rating))
        comment = request.form.get('comment', '')

        review = Review(
            booking_id=booking.id,
            reviewer_id=current_user.id,
            sitter_profile_id=booking.sitter_id,
            rating=rating,
            comment=comment,
        )
        db.session.add(review)
        db.session.commit()

        recalculate_sitter_rating(booking.sitter)
        flash('Thank you for your review!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('review.html', booking=booking)
