from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'owner' or 'sitter'
    phone = db.Column(db.String(30))
    avatar_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sitter_profile = db.relationship(
        'SitterProfile', backref='user', uselist=False, cascade='all, delete-orphan'
    )
    bookings_as_owner = db.relationship(
        'Booking', foreign_keys='Booking.owner_id', backref='owner'
    )
    reviews_given = db.relationship(
        'Review', foreign_keys='Review.reviewer_id', backref='reviewer'
    )
    messages_sent = db.relationship(
        'Message', foreign_keys='Message.sender_id', backref='sender'
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.email}>'


class SitterProfile(db.Model):
    __tablename__ = 'sitter_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    bio = db.Column(db.Text)
    city = db.Column(db.String(100), index=True)
    country = db.Column(db.String(50), default='Portugal', index=True)
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
    # Environment / housing (Rover-style filters)
    has_fenced_yard = db.Column(db.Boolean, default=False)
    owns_dog = db.Column(db.Boolean, default=False)
    owns_cat = db.Column(db.Boolean, default=False)
    one_client_only = db.Column(db.Boolean, default=False)
    has_children = db.Column(db.Boolean, default=False)
    accepts_unspayed_female = db.Column(db.Boolean, default=True)
    accepts_intact_male = db.Column(db.Boolean, default=True)
    offers_grooming = db.Column(db.Boolean, default=False)
    is_star_sitter = db.Column(db.Boolean, default=False)
    availability_notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    photo_url = db.Column(db.String(300))
    avg_rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)

    reviews = db.relationship('Review', backref='sitter_profile', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='sitter', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<SitterProfile {self.id} {self.city}>'


class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sitter_id = db.Column(db.Integer, db.ForeignKey('sitter_profile.id'), nullable=False, index=True)
    service_type = db.Column(db.String(30), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    dog_name = db.Column(db.String(80))
    dog_breed = db.Column(db.String(80))
    dog_size = db.Column(db.String(20))
    notes = db.Column(db.Text)
    total_price = db.Column(db.Float)
    # pending (awaiting sitter), confirmed, declined, completed, cancelled
    status = db.Column(db.String(20), default='pending', index=True)
    # unpaid, authorized, captured, refunded
    payment_status = db.Column(db.String(20), default='unpaid')
    stripe_session_id = db.Column(db.String(200))
    stripe_payment_intent_id = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship(
        'Message', backref='booking', cascade='all, delete-orphan',
        order_by='Message.created_at'
    )
    review = db.relationship('Review', backref='booking', uselist=False, cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Booking {self.id} {self.status}>'


class Review(db.Model):
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), unique=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sitter_profile_id = db.Column(db.Integer, db.ForeignKey('sitter_profile.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
