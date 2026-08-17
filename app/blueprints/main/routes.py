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

    # Pet filter params (Rover-style)
    dogs = request.args.get('dogs', default=1, type=int) or 0
    puppies = request.args.get('puppies', default=0, type=int) or 0
    cats = request.args.get('cats', default=0, type=int) or 0
    # sizes: comma-separated small,medium,large,giant
    sizes_raw = request.args.get('sizes', '')
    sizes = [s.strip() for s in sizes_raw.split(',') if s.strip()]
    dogs_dislike_cats = request.args.get('dogs_dislike_cats') == '1'

    dogs = max(0, min(dogs, 10))
    puppies = max(0, min(puppies, 10))
    cats = max(0, min(cats, 10))
    total_dogs = dogs + puppies

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

    # Capacity: sitter must accept at least this many dogs
    if total_dogs > 0:
        query = query.filter(SitterProfile.max_dogs >= total_dogs)

    # Puppies
    if puppies > 0:
        query = query.filter_by(accepts_puppies=True)

    # Large / giant dogs
    if 'large' in sizes or 'giant' in sizes:
        query = query.filter_by(accepts_large_dogs=True)

    sitters = query.order_by(SitterProfile.avg_rating.desc()).all()

    # Pet summary label for the bar
    pet_parts = []
    if dogs:
        pet_parts.append(f'{dogs} dog{"s" if dogs != 1 else ""}')
    if puppies:
        pet_parts.append(f'{puppies} puppy' if puppies == 1 else f'{puppies} puppies')
    if cats:
        pet_parts.append(f'{cats} cat{"s" if cats != 1 else ""}')
    pet_label = ', '.join(pet_parts) if pet_parts else '1 dog'

    return render_template(
        'search.html',
        sitters=sitters,
        city=city,
        country=country,
        service=service,
        dogs=dogs,
        puppies=puppies,
        cats=cats,
        sizes=sizes,
        dogs_dislike_cats=dogs_dislike_cats,
        pet_label=pet_label,
        min_rating=min_rating,
    )


@bp.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500
