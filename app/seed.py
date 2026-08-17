from app.extensions import db
from app.models import User, SitterProfile


def seed_data() -> None:
    if User.query.count() > 0:
        print('Database already has users — skip seed.')
        return

    demos = [
        {
            'email': 'maria@example.com', 'name': 'Maria Santos', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Passionate dog lover with 8 years of experience. Big backyard and treat every dog like family.',
                'city': 'Lisbon', 'country': 'Portugal', 'address': 'Alfama, Lisbon',
                'lat': 38.7114, 'lng': -9.1300,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 35, 'price_walking_hour': 15, 'price_daycare_day': 25,
                'max_dogs': 3, 'years_experience': 8, 'home_type': 'house', 'has_yard': True,
                'availability_notes': 'Available most weekdays and weekends.',
            },
        },
        {
            'email': 'joao@example.com', 'name': 'João Pereira', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Professional dog walker. Live near parks, love long walks.',
                'city': 'Porto', 'country': 'Portugal', 'address': 'Cedofeita, Porto',
                'lat': 41.1579, 'lng': -8.6291,
                'offers_boarding': False, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 0, 'price_walking_hour': 12, 'price_daycare_day': 20,
                'max_dogs': 2, 'years_experience': 4, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Flexible schedule.',
            },
        },
        {
            'email': 'sofia@example.com', 'name': 'Sofia Costa', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Quiet countryside home, perfect for anxious or senior dogs.',
                'city': 'Sintra', 'country': 'Portugal', 'address': 'Near Sintra Parque',
                'lat': 38.8029, 'lng': -9.3817,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': False,
                'price_boarding_day': 40, 'price_walking_hour': 18, 'price_daycare_day': 0,
                'max_dogs': 4, 'years_experience': 12, 'home_type': 'farm', 'has_yard': True,
                'availability_notes': 'Ideal for longer stays.',
            },
        },
        {
            'email': 'ana.faro@example.com', 'name': 'Ana Rodrigues', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Beach lover in the Algarve. Daily walks on the sand.',
                'city': 'Faro', 'country': 'Portugal', 'address': 'Old Town Faro',
                'lat': 37.0194, 'lng': -7.9322,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 30, 'price_walking_hour': 14, 'price_daycare_day': 22,
                'max_dogs': 2, 'years_experience': 5, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Great for summer stays.',
            },
        },
        {
            'email': 'carlos@example.com', 'name': 'Carlos Mendoza', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Madrid-based sitter with a large terrace.',
                'city': 'Madrid', 'country': 'Spain', 'address': 'Chamberí',
                'lat': 40.4340, 'lng': -3.7035,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 38, 'price_walking_hour': 16, 'price_daycare_day': 28,
                'max_dogs': 2, 'years_experience': 6, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Available evenings and weekends.',
            },
        },
        {
            'email': 'lucia@example.com', 'name': 'Lucía Fernández', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Barcelona beach walks every morning.',
                'city': 'Barcelona', 'country': 'Spain', 'address': 'Barceloneta',
                'lat': 41.3809, 'lng': 2.1898,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': False,
                'price_boarding_day': 42, 'price_walking_hour': 18, 'price_daycare_day': 0,
                'max_dogs': 1, 'years_experience': 7, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Prefer small and medium dogs.',
            },
        },
        {
            'email': 'pierre@example.com', 'name': 'Pierre Dubois', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Parisian with a soft spot for dogs. Quiet flat near parks.',
                'city': 'Paris', 'country': 'France', 'address': 'Le Marais',
                'lat': 48.8566, 'lng': 2.3522,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 45, 'price_walking_hour': 20, 'price_daycare_day': 30,
                'max_dogs': 1, 'years_experience': 9, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Available weekdays.',
            },
        },
        {
            'email': 'giulia@example.com', 'name': 'Giulia Rossi', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Rome countryside villa. Dogs can run free all day.',
                'city': 'Rome', 'country': 'Italy', 'address': 'Near Appia Antica',
                'lat': 41.8560, 'lng': 12.5200,
                'offers_boarding': True, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 40, 'price_walking_hour': 15, 'price_daycare_day': 25,
                'max_dogs': 5, 'years_experience': 10, 'home_type': 'house', 'has_yard': True,
                'availability_notes': 'Ideal for multiple dogs.',
            },
        },
        {
            'email': 'hans@example.com', 'name': 'Hans Müller', 'role': 'sitter', 'password': 'demo123',
            'profile': {
                'bio': 'Berlin dog lover. Long forest walks every day.',
                'city': 'Berlin', 'country': 'Germany', 'address': 'Prenzlauer Berg',
                'lat': 52.5388, 'lng': 13.4240,
                'offers_boarding': False, 'offers_walking': True, 'offers_daycare': True,
                'price_boarding_day': 0, 'price_walking_hour': 17, 'price_daycare_day': 27,
                'max_dogs': 3, 'years_experience': 5, 'home_type': 'apartment', 'has_yard': False,
                'availability_notes': 'Morning and afternoon slots.',
            },
        },
        {
            'email': 'owner@example.com', 'name': 'Ana Owner', 'role': 'owner', 'password': 'demo123',
            'profile': None,
        },
    ]

    for u in demos:
        user = User(email=u['email'], name=u['name'], role=u['role'])
        user.set_password(u['password'])
        db.session.add(user)
        db.session.flush()
        if u['profile']:
            p = dict(u['profile'])
            profile = SitterProfile(user_id=user.id, **p)
            profile.avg_rating = round(4.2 + (hash(u['email']) % 8) / 10, 1)
            profile.review_count = 5 + (hash(u['email']) % 20)
            # Environment defaults from home type
            ht = p.get('home_type') or ''
            profile.has_fenced_yard = bool(p.get('has_yard')) or ht in ('house', 'farm')
            profile.owns_dog = (hash(u['email']) % 3) == 0
            profile.owns_cat = (hash(u['email']) % 4) == 0
            profile.has_children = (hash(u['email']) % 5) == 0
            profile.one_client_only = ht == 'apartment'
            profile.accepts_unspayed_female = True
            profile.accepts_intact_male = True
            profile.offers_grooming = (hash(u['email']) % 3) == 1
            profile.is_star_sitter = profile.avg_rating >= 4.7
            db.session.add(profile)

    db.session.commit()
    print('Demo data seeded.')
