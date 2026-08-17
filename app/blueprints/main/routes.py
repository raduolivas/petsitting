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

    dogs = request.args.get('dogs', default=1, type=int) or 0
    puppies = request.args.get('puppies', default=0, type=int) or 0
    cats = request.args.get('cats', default=0, type=int) or 0
    sizes_raw = request.args.get('sizes', '')
    sizes = [s.strip() for s in sizes_raw.split(',') if s.strip()]
    dogs_dislike_cats = request.args.get('dogs_dislike_cats') == '1'

    # Environment filters (Rover-style)
    star_only = request.args.get('star') == '1'
    has_house = request.args.get('has_house') == '1'
    has_fenced_yard = request.args.get('has_fenced_yard') == '1'
    no_dog = request.args.get('no_dog') == '1'
    no_cat = request.args.get('no_cat') == '1'
    one_client = request.args.get('one_client') == '1'
    no_children = request.args.get('no_children') == '1'
    unspayed = request.args.get('unspayed') == '1'
    intact_male = request.args.get('intact_male') == '1'
    grooming = request.args.get('grooming') == '1'

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

    if total_dogs > 0:
        query = query.filter(SitterProfile.max_dogs >= total_dogs)
    if puppies > 0:
        query = query.filter_by(accepts_puppies=True)
    if 'large' in sizes or 'giant' in sizes:
        query = query.filter_by(accepts_large_dogs=True)

    if star_only:
        query = query.filter(
            (SitterProfile.is_star_sitter.is_(True)) | (SitterProfile.avg_rating >= 4.8)
        )
    if has_house:
        query = query.filter(SitterProfile.home_type.in_(['house', 'farm']))
    if has_fenced_yard:
        query = query.filter(
            (SitterProfile.has_fenced_yard.is_(True)) | (SitterProfile.has_yard.is_(True))
        )
    if no_dog:
        query = query.filter_by(owns_dog=False)
    if no_cat:
        query = query.filter_by(owns_cat=False)
    if one_client:
        query = query.filter_by(one_client_only=True)
    if no_children:
        query = query.filter_by(has_children=False)
    if unspayed:
        query = query.filter_by(accepts_unspayed_female=True)
    if intact_male:
        query = query.filter_by(accepts_intact_male=True)
    if grooming:
        query = query.filter_by(offers_grooming=True)
    if dogs_dislike_cats:
        query = query.filter_by(owns_cat=False)

    sitters = query.order_by(SitterProfile.avg_rating.desc()).all()

    pet_parts = []
    if dogs:
        pet_parts.append(f'{dogs} dog{"s" if dogs != 1 else ""}')
    if puppies:
        pet_parts.append(f'{puppies} puppy' if puppies == 1 else f'{puppies} puppies')
    if cats:
        pet_parts.append(f'{cats} cat{"s" if cats != 1 else ""}')
    pet_label = ', '.join(pet_parts) if pet_parts else '1 dog'

    env_flags = {
        'star': star_only,
        'has_house': has_house,
        'has_fenced_yard': has_fenced_yard,
        'no_dog': no_dog,
        'no_cat': no_cat,
        'one_client': one_client,
        'no_children': no_children,
        'unspayed': unspayed,
        'intact_male': intact_male,
        'grooming': grooming,
    }
    active_filter_count = sum(1 for v in env_flags.values() if v)

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
        env=env_flags,
        active_filter_count=active_filter_count,
    )


@bp.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500
