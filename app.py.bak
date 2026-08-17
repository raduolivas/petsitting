from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
import json

# Optional Stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pawbnb-mvp-secret-key-change-in-production')
# Prefer instance/ folder, fall back to /tmp if needed
_db_path = os.path.join(os.path.dirname(__file__), 'instance', 'pawbnb.db')
os.makedirs(os.path.dirname(_db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + _db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Stripe config (use test keys – replace with your own)
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')  # sk_test_...
app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')  # pk_test_...
app.config['STRIPE_WEBHOOK_SECRET'] = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

if STRIPE_AVAILABLE and app.config['STRIPE_SECRET_KEY']:
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ==================== MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'owner' or 'sitter'
    phone = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sitter_profile = db.relationship('SitterProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    bookings_as_owner = db.relationship('Booking', foreign_keys='Booking.owner_id', backref='owner')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', backref='reviewer')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SitterProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bio = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(50), default='Portugal')
    address = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    offers_boarding = db.Column(db.Boolean, default=False)
    offers_walking = db.Column(db.Boolean, default=False)
    offers_daycare = db.Column(db.Boolean, default=False)
    price_boarding_day = db.Column(db.Float, default=0)
    price_walking_hour = db.Column(db.Float, default=0)
    price_daycare_day = db.Column(db.Float, default=0)
    max_dogs = db.Column(db.Integer, default=1)
    years_experience = db.Column(db.Integer, default=0)
    home_type = db.Column(db.String(50))
    has_yard = db.Column(db.Boolean, default=False)
    accepts_puppies = db.Column(db.Boolean, default=True)
    accepts_large_dogs = db.Column(db.Boolean, default=True)
    availability_notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    avg_rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)

    reviews = db.relationship('Review', backref='sitter_profile', cascade='all, delete-orphan')


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sitter_id = db.Column(db.Integer, db.ForeignKey('sitter_profile.id'), nullable=False)
    service_type = db.Column(db.String(30), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    dog_name = db.Column(db.String(80))
    dog_breed = db.Column(db.String(80))
    dog_size = db.Column(db.String(20))
    notes = db.Column(db.Text)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, refunded
    stripe_session_id = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sitter = db.relationship('SitterProfile', backref='bookings')
    messages = db.relationship('Message', backref='booking', cascade='all, delete-orphan', order_by='Message.created_at')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), unique=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sitter_profile_id = db.Column(db.Integer, db.ForeignKey('sitter_profile.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship('Booking', backref=db.backref('review', uselist=False))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ==================== HELPERS ====================

def can_access_booking(booking):
    """Owner or the sitter of this booking."""
    if not current_user.is_authenticated:
        return False
    if booking.owner_id == current_user.id:
        return True
    profile = current_user.sitter_profile
    if profile and booking.sitter_id == profile.id:
        return True
    return False


# ==================== ROUTES ====================

@app.route('/')
def index():
    sitters = SitterProfile.query.filter_by(is_active=True).order_by(SitterProfile.avg_rating.desc()).limit(6).all()
    return render_template('index.html', sitters=sitters)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'owner')
        phone = request.form.get('phone', '').strip()

        if not email or not name or not password:
            flash('Please fill all required fields.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        user = User(email=email, name=name, role=role, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role == 'sitter':
            profile = SitterProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()

        login_user(user)
        flash(f'Welcome to Pawbnb, {name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'sitter':
        profile = current_user.sitter_profile
        bookings = Booking.query.filter_by(sitter_id=profile.id).order_by(Booking.created_at.desc()).all() if profile else []
        return render_template('dashboard_sitter.html', profile=profile, bookings=bookings)
    else:
        bookings = Booking.query.filter_by(owner_id=current_user.id).order_by(Booking.created_at.desc()).all()
        return render_template('dashboard_owner.html', bookings=bookings)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'sitter':
        flash('Only sitters can edit a care profile.', 'error')
        return redirect(url_for('dashboard'))

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

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_profile.html', profile=profile)


@app.route('/search')
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
    return render_template('search.html', sitters=sitters, city=city, country=country, service=service)


@app.route('/sitter/<int:profile_id>')
def sitter_profile(profile_id):
    profile = SitterProfile.query.get_or_404(profile_id)
    reviews = Review.query.filter_by(sitter_profile_id=profile_id).order_by(Review.created_at.desc()).all()
    return render_template('sitter_profile.html', profile=profile, reviews=reviews)


@app.route('/book/<int:profile_id>', methods=['GET', 'POST'])
@login_required
def book(profile_id):
    if current_user.role != 'owner':
        flash('Only pet owners can make bookings.', 'error')
        return redirect(url_for('sitter_profile', profile_id=profile_id))

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
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date
        except (ValueError, TypeError):
            flash('Invalid dates.', 'error')
            return redirect(url_for('book', profile_id=profile_id))

        days = max((end_date - start_date).days + 1, 1)
        if service_type == 'boarding':
            total = profile.price_boarding_day * days
        elif service_type == 'daycare':
            total = profile.price_daycare_day * days
        elif service_type == 'walking':
            total = profile.price_walking_hour * days  # 1h per day simplified
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
            payment_status='unpaid'
        )
        db.session.add(booking)
        db.session.commit()

        flash('Booking created! Please complete payment.', 'success')
        return redirect(url_for('payment', booking_id=booking.id))

    return render_template('book.html', profile=profile)


@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.owner_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('dashboard'))

    if booking.payment_status == 'paid':
        flash('This booking is already paid.', 'info')
        return redirect(url_for('booking_detail', booking_id=booking.id))

    use_stripe = STRIPE_AVAILABLE and bool(app.config['STRIPE_SECRET_KEY'])

    if request.method == 'POST':
        # Mock payment fallback (or when Stripe not configured)
        if request.form.get('method') == 'mock' or not use_stripe:
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            db.session.commit()
            flash('Payment successful! Booking confirmed. 🎉', 'success')
            return redirect(url_for('booking_detail', booking_id=booking.id))

        # Stripe Checkout
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'Pawbnb – {booking.service_type.title()} for {booking.dog_name}',
                            'description': f'{booking.start_date} to {booking.end_date or booking.start_date}',
                        },
                        'unit_amount': int(booking.total_price * 100),  # cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=url_for('payment_success', booking_id=booking.id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('payment', booking_id=booking.id, _external=True),
                metadata={'booking_id': str(booking.id)},
            )
            booking.stripe_session_id = session.id
            db.session.commit()
            return redirect(session.url, code=303)
        except Exception as e:
            flash(f'Stripe error: {str(e)}. Using demo payment instead.', 'error')
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            db.session.commit()
            return redirect(url_for('booking_detail', booking_id=booking.id))

    return render_template('payment.html', booking=booking, use_stripe=use_stripe,
                           stripe_pk=app.config.get('STRIPE_PUBLISHABLE_KEY', ''))


@app.route('/payment/success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.owner_id != current_user.id:
        abort(403)

    session_id = request.args.get('session_id')
    if session_id and STRIPE_AVAILABLE and app.config['STRIPE_SECRET_KEY']:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                booking.payment_status = 'paid'
                booking.status = 'confirmed'
                booking.stripe_session_id = session_id
                db.session.commit()
                flash('Payment successful via Stripe! Booking confirmed. 🎉', 'success')
            else:
                flash('Payment not completed.', 'error')
        except Exception:
            flash('Could not verify Stripe payment. Please contact support.', 'error')
    else:
        # Fallback
        booking.payment_status = 'paid'
        booking.status = 'confirmed'
        db.session.commit()
        flash('Payment successful! Booking confirmed. 🎉', 'success')

    return redirect(url_for('booking_detail', booking_id=booking.id))


@app.route('/booking/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not can_access_booking(booking):
        flash('Unauthorized.', 'error')
        return redirect(url_for('dashboard'))

    # Mark messages as read for current user
    for msg in booking.messages:
        if msg.sender_id != current_user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return render_template('booking_detail.html', booking=booking)


@app.route('/booking/<int:booking_id>/message', methods=['POST'])
@login_required
def send_message(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not can_access_booking(booking):
        flash('Unauthorized.', 'error')
        return redirect(url_for('dashboard'))

    content = request.form.get('content', '').strip()
    if not content:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('booking_detail', booking_id=booking_id))

    msg = Message(
        booking_id=booking.id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()
    flash('Message sent!', 'success')
    return redirect(url_for('booking_detail', booking_id=booking_id))


@app.route('/booking/<int:booking_id>/complete', methods=['POST'])
@login_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not can_access_booking(booking):
        flash('Unauthorized.', 'error')
        return redirect(url_for('dashboard'))

    booking.status = 'completed'
    db.session.commit()
    flash('Booking marked as completed. You can now leave a review!', 'success')
    return redirect(url_for('booking_detail', booking_id=booking_id))


@app.route('/review/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def leave_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.owner_id != current_user.id:
        flash('Only the owner can leave a review.', 'error')
        return redirect(url_for('dashboard'))
    if booking.status != 'completed':
        flash('You can only review completed bookings.', 'error')
        return redirect(url_for('dashboard'))
    if booking.review:
        flash('You already reviewed this booking.', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        comment = request.form.get('comment', '')

        review = Review(
            booking_id=booking.id,
            reviewer_id=current_user.id,
            sitter_profile_id=booking.sitter_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)

        profile = booking.sitter
        reviews = Review.query.filter_by(sitter_profile_id=profile.id).all()
        if reviews:
            profile.avg_rating = sum(r.rating for r in reviews) / len(reviews)
            profile.review_count = len(reviews)
        db.session.commit()

        flash('Thank you for your review!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('review.html', booking=booking)


@app.route('/api/sitters')
def api_sitters():
    city = request.args.get('city', '').strip()
    country = request.args.get('country', '').strip()
    query = SitterProfile.query.filter_by(is_active=True).filter(SitterProfile.lat.isnot(None))
    if city:
        query = query.filter(SitterProfile.city.ilike(f'%{city}%'))
    if country:
        query = query.filter(SitterProfile.country.ilike(f'%{country}%'))

    sitters = query.all()
    data = []
    for s in sitters:
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
            'url': url_for('sitter_profile', profile_id=s.id)
        })
    return jsonify(data)


# ==================== SEED DATA ====================

def seed_data():
    if User.query.count() > 0:
        return

    demos = [
        # Portugal
        {
            'email': 'maria@example.com', 'name': 'Maria Santos', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Passionate dog lover with 8 years of experience. Big backyard and treat every dog like family. Available for boarding and walks.',
                'city': 'Lisbon', 'country': 'Portugal', 'address': 'Alfama, Lisbon',
                'lat': 38.7114, 'lng': -9.1300,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 35, 'price_walking_hour': 15, 'price_daycare_day': 25,
                'max_dogs': 3, 'years_experience': 8, 'home_type': 'house', 'has_yard': True,
                'availability_notes': 'Available most weekdays and weekends. Prefer medium/large dogs.'
            }
        },
        {
            'email': 'joao@example.com', 'name': 'João Pereira', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Professional dog walker and sitter. Live near parks, love long walks. Perfect for energetic dogs.',
                'city': 'Porto', 'country': 'Portugal', 'address': 'Cedofeita, Porto',
                'lat': 41.1579, 'lng': -8.6291,
                'offers_boarding': False, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 0, 'price_walking_hour': 12, 'price_daycare_day': 20,
                'max_dogs': 2, 'years_experience': 4, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Flexible schedule. Morning and evening walks available.'
            }
        },
        {
            'email': 'sofia@example.com', 'name': 'Sofia Costa', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Quiet countryside home, perfect for anxious or senior dogs. Lots of space to run free.',
                'city': 'Sintra', 'country': 'Portugal', 'address': 'Near Sintra Parque',
                'lat': 38.8029, 'lng': -9.3817,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': False,
                'price_boarding_day': 40, 'price_walking_hour': 18, 'price_daycare_day': 0,
                'max_dogs': 4, 'years_experience': 12, 'home_type': 'farm', 'has_yard': True,
                'availability_notes': 'Ideal for longer stays (3+ days).'
            }
        },
        {
            'email': 'ana.faro@example.com', 'name': 'Ana Rodrigues', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Beach lover in the Algarve. Daily walks on the sand and lots of sunshine for your pup.',
                'city': 'Faro', 'country': 'Portugal', 'address': 'Old Town Faro',
                'lat': 37.0194, 'lng': -7.9322,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 30, 'price_walking_hour': 14, 'price_daycare_day': 22,
                'max_dogs': 2, 'years_experience': 5, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Great for summer stays.'
            }
        },
        # Spain
        {
            'email': 'carlos@example.com', 'name': 'Carlos Mendoza', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Madrid-based sitter with a large terrace. Experienced with all breeds including reactive dogs.',
                'city': 'Madrid', 'country': 'Spain', 'address': 'Chamberí',
                'lat': 40.4340, 'lng': -3.7035,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 38, 'price_walking_hour': 16, 'price_daycare_day': 28,
                'max_dogs': 2, 'years_experience': 6, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Available evenings and weekends.'
            }
        },
        {
            'email': 'lucia@example.com', 'name': 'Lucía Fernández', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Barcelona beach walks every morning. Your dog will love the Mediterranean lifestyle!',
                'city': 'Barcelona', 'country': 'Spain', 'address': 'Barceloneta',
                'lat': 41.3809, 'lng': 2.1898,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': False,
                'price_boarding_day': 42, 'price_walking_hour': 18, 'price_daycare_day': 0,
                'max_dogs': 1, 'years_experience': 7, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Prefer small and medium dogs.'
            }
        },
        # France
        {
            'email': 'pierre@example.com', 'name': 'Pierre Dubois', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Parisian with a soft spot for dogs. Quiet flat near parks, perfect for city pups.',
                'city': 'Paris', 'country': 'France', 'address': 'Le Marais',
                'lat': 48.8566, 'lng': 2.3522,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 45, 'price_walking_hour': 20, 'price_daycare_day': 30,
                'max_dogs': 1, 'years_experience': 9, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Available weekdays.'
            }
        },
        # Italy
        {
            'email': 'giulia@example.com', 'name': 'Giulia Rossi', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Rome countryside villa. Dogs can run free all day in a big secure garden.',
                'city': 'Rome', 'country': 'Italy', 'address': 'Near Appia Antica',
                'lat': 41.8560, 'lng': 12.5200,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 40, 'price_walking_hour': 15, 'price_daycare_day': 25,
                'max_dogs': 5, 'years_experience': 10, 'home_type': 'house', 'has_yard': True,
                'availability_notes': 'Ideal for multiple dogs and longer stays.'
            }
        },
        # Germany
        {
            'email': 'hans@example.com', 'name': 'Hans Müller', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Berlin dog lover. Very active – long forest walks every day. Great with high-energy breeds.',
                'city': 'Berlin', 'country': 'Germany', 'address': 'Prenzlauer Berg',
                'lat': 52.5388, 'lng': 13.4240,
                'offers_boarding': False, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 0, 'price_walking_hour': 17, 'price_daycare_day': 27,
                'max_dogs': 3, 'years_experience': 5, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Morning and afternoon slots.'
            }
        },
        # Owner
        {
            'email': 'owner@example.com', 'name': 'Ana Owner', 'role': 'owner', 'password': 'demo123',
            'profile': None
        },
    ]

    for u in demos:
        user = User(email=u['email'], name=u['name'], role=u['role'])
        user.set_password(u['password'])
        db.session.add(user)
        db.session.flush()
        if u['profile']:
            p = u['profile']
            profile = SitterProfile(user_id=user.id, **p)
            profile.avg_rating = round(4.2 + (hash(u['email']) % 8) / 10, 1)  # 4.2–4.9
            profile.review_count = 5 + (hash(u['email']) % 20)
            db.session.add(profile)

    db.session.commit()
    print("Demo data seeded with multiple cities!")


with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
