def test_register_owner(client, app):
    r = client.post('/register', data={
        'email': 'new@example.com',
        'name': 'New User',
        'password': 'secret12',
        'role': 'owner',
    }, follow_redirects=True)
    assert r.status_code == 200
    from app.models import User
    with app.app_context():
        assert User.query.filter_by(email='new@example.com').first() is not None


def test_login_logout(client, owner):
    r = client.post('/login', data={
        'email': 'owner@test.com',
        'password': 'password123',
    }, follow_redirects=True)
    assert r.status_code == 200
    r = client.get('/logout', follow_redirects=True)
    assert r.status_code == 200


def test_login_bad_password(client, owner):
    r = client.post('/login', data={
        'email': 'owner@test.com',
        'password': 'wrong',
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'Invalid' in r.data or b'invalid' in r.data.lower()
