def test_book_requires_login(client, sitter):
    from app.models import SitterProfile
    from app.extensions import db
    profile = SitterProfile.query.first()
    r = client.get(f'/book/{profile.id}')
    # should redirect to login
    assert r.status_code in (302, 401)


def test_search_pet_filter(client, sitter):
    r = client.get('/search?dogs=2&puppies=1&sizes=large')
    assert r.status_code == 200
