from flask import jsonify, request, url_for
from app.blueprints.api import bp
from app.models import SitterProfile
from app.services.booking_service import get_blocked_dates
from app.extensions import csrf


@bp.route('/health')
@csrf.exempt
def health():
    return jsonify({'status': 'ok', 'service': 'pawbnb'}), 200


@bp.route('/sitters')
def sitters():
    city = request.args.get('city', '').strip()
    country = request.args.get('country', '').strip()
    query = SitterProfile.query.filter_by(is_active=True).filter(
        SitterProfile.lat.isnot(None)
    )
    if city:
        query = query.filter(SitterProfile.city.ilike(f'%{city}%'))
    if country:
        query = query.filter(SitterProfile.country.ilike(f'%{country}%'))

    data = []
    for s in query.all():
        data.append({
            'id': s.id,
            'name': s.user.name,
            'city': s.city,
            'country': s.country,
            'lat': s.lat,
            'lng': s.lng,
            'rating': s.avg_rating,
            'price_boarding': s.price_boarding_day,
            'offers_boarding': s.offers_boarding,
            'offers_walking': s.offers_walking,
            'offers_daycare': s.offers_daycare,
            'url': url_for('sitters.profile', profile_id=s.id),
        })
    return jsonify(data)


@bp.route('/sitter/<int:profile_id>/blocked-dates')
def blocked_dates(profile_id):
    return jsonify(get_blocked_dates(profile_id))
