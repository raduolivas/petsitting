from datetime import timedelta
from app.models import Booking
from app.extensions import db


def get_blocked_dates(sitter_profile_id: int) -> list[str]:
    """Return list of YYYY-MM-DD strings already booked (pending or confirmed)."""
    blocked = set()
    bookings = Booking.query.filter(
        Booking.sitter_id == sitter_profile_id,
        Booking.status.in_(['pending', 'confirmed']),
    ).all()
    for b in bookings:
        d = b.start_date
        end = b.end_date or b.start_date
        while d <= end:
            blocked.add(d.isoformat())
            d += timedelta(days=1)
    return sorted(blocked)


def dates_overlap(start1, end1, start2, end2) -> bool:
    end1 = end1 or start1
    end2 = end2 or start2
    return start1 <= end2 and start2 <= end1


def can_access_booking(booking, user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if booking.owner_id == user.id:
        return True
    profile = user.sitter_profile
    if profile and booking.sitter_id == profile.id:
        return True
    return False


def recalculate_sitter_rating(profile) -> None:
    from app.models import Review
    reviews = Review.query.filter_by(sitter_profile_id=profile.id).all()
    if reviews:
        profile.avg_rating = sum(r.rating for r in reviews) / len(reviews)
        profile.review_count = len(reviews)
    else:
        profile.avg_rating = 0.0
        profile.review_count = 0
    db.session.commit()
