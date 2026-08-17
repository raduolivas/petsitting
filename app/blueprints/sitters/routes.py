from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.blueprints.sitters import bp
from app.extensions import db
from app.models import SitterProfile, Review
from app.services.upload_service import save_sitter_photo


@bp.route('/sitter/<int:profile_id>')
def profile(profile_id):
    profile = SitterProfile.query.get_or_404(profile_id)
    reviews = (
        Review.query.filter_by(sitter_profile_id=profile_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return render_template('sitter_profile.html', profile=profile, reviews=reviews)


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'sitter':
        flash('Only sitters can edit a care profile.', 'error')
        return redirect(url_for('main.dashboard'))

    profile = current_user.sitter_profile
    if not profile:
        profile = SitterProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    if request.method == 'POST':
        profile.bio = request.form.get('bio', '')
        profile.city = request.form.get('city', '')
        profile.country = request.form.get('country', 'Portugal')
        profile.address = request.form.get('address', '')
        try:
            lat_val = request.form.get('lat')
            lng_val = request.form.get('lng')
            profile.lat = float(lat_val) if lat_val else None
            profile.lng = float(lng_val) if lng_val else None
        except ValueError:
            profile.lat = None
            profile.lng = None

        profile.offers_boarding = 'offers_boarding' in request.form
        profile.offers_walking = 'offers_walking' in request.form
        profile.offers_daycare = 'offers_daycare' in request.form

        profile.price_boarding_day = float(request.form.get('price_boarding_day') or 0)
        profile.price_walking_hour = float(request.form.get('price_walking_hour') or 0)
        profile.price_daycare_day = float(request.form.get('price_daycare_day') or 0)

        profile.max_dogs = int(request.form.get('max_dogs') or 1)
        profile.years_experience = int(request.form.get('years_experience') or 0)
        profile.home_type = request.form.get('home_type', '')
        profile.has_yard = 'has_yard' in request.form
        profile.accepts_puppies = 'accepts_puppies' in request.form
        profile.accepts_large_dogs = 'accepts_large_dogs' in request.form
        profile.availability_notes = request.form.get('availability_notes', '')
        profile.is_active = 'is_active' in request.form

        photo = request.files.get('photo')
        if photo and photo.filename:
            try:
                url = save_sitter_photo(photo, current_user.id)
                if url:
                    profile.photo_url = url
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('sitters.edit_profile'))

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('edit_profile.html', profile=profile)
