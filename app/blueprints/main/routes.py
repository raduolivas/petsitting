from flask import render_template, request
from flask_login import login_required, current_user
from app.blueprints.main import bp
from app.models import SitterProfile, Booking


@bp.route('/')
def index():
    sitters = (
        SitterProfile.query.filter_by(is_active=True)
        .order_by(SitterProfile.avg_rating.desc())
        .limit(6)
        .all()
    )
    return render_template('index.html', sitters=sitters)


@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'sitter':
        profile = current_user.sitter_profile
        bookings = []
        if profile:
            bookings = (
                Booking.query.filter_by(sitter_id=profile.id)
                .order_by(Booking.created_at.desc())
                .all()
            )
        return render_template('dashboard_sitter.html', profile=profile, bookings=bookings)

    bookings = (
        Booking.query.filter_by(owner_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template('dashboard_owner.html', bookings=bookings)


@bp.route('/search')
def search():
    city = request.args.get('city', '').strip()
    country = request.args.get('country', '').strip()
    service = request.args.get('service', '')
    min_rating = request.args.get('min_rating', type=float)

    query = SitterProfile.query.filter_by(is_active=True)

    if city:
        query = query.filter(SitterProfile.city.ilike(f'%{city}%'))
    if country:
        query = query.filter(SitterProfile.country.ilike(f'%{country}%'))
    if service == 'boarding':
        query = query.filter_by(offers_boarding=True)
    elif service == 'walking':
        query = query.filter_by(offers_walking=True)
    elif service == 'daycare':
        query = query.filter_by(offers_daycare=True)
    if min_rating:
        query = query.filter(SitterProfile.avg_rating >= min_rating)

    sitters = query.order_by(SitterProfile.avg_rating.desc()).all()
    return render_template(
        'search.html', sitters=sitters, city=city, country=country, service=service
    )


@bp.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500
