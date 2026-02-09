def test_get_user_success(client):
    resp = client.get("/users/123")
    assert resp.status_code == 200

def test_get_user_not_found(client):
    resp = client.get("/users/999")
    assert resp.status_code == 404

def test_put_user_success(client):
    resp = client.put("/users/123", json={"name": "Alice"})
    assert resp.status_code == 200

def test_put_user_not_found(client):
    resp = client.put("/users/999", json={"name": "Alice"})
    assert resp.status_code == 404

def test_put_user_forbidden(client):
    resp = client.put("/users/123", json={"name": "Alice"})
    assert resp.status_code == 403
