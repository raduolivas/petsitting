def test_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'ok'


def test_home_page(client):
    r = client.get('/')
    assert r.status_code == 200
    assert b'Pawbnb' in r.data or b'pet' in r.data.lower()


def test_search_page(client):
    r = client.get('/search')
    assert r.status_code == 200
