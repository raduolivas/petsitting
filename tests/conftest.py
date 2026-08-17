import pytest
from app import create_app
from app.extensions import db
from app.models import User, SitterProfile


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def owner(app):
    user = User(email='owner@test.com', name='Test Owner', role='owner')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sitter(app):
    user = User(email='sitter@test.com', name='Test Sitter', role='sitter')
    user.set_password('password123')
    db.session.add(user)
    db.session.flush()
    profile = SitterProfile(
        user_id=user.id,
        city='Lisbon',
        country='Portugal',
        offers_boarding=True,
        price_boarding_day=30,
        max_dogs=3,
        accepts_puppies=True,
        accepts_large_dogs=True,
        is_active=True,
        lat=38.72,
        lng=-9.14,
    )
    db.session.add(profile)
    db.session.commit()
    return user
