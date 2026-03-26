import time


def test_register(client):
    unique_value = str(int(time.time()))
    response = client.post("/api/register", json={
        "username": f"testuser_{unique_value}",
        "email": f"test_{unique_value}@test.com",
        "password": "123456"
    })

    assert response.status_code == 201


def test_login(client):
    unique_value = str(int(time.time()))

    register_response = client.post("/api/register", json={
        "username": f"loginuser_{unique_value}",
        "email": f"login_{unique_value}@test.com",
        "password": "123456"
    })

    assert register_response.status_code == 201

    login_response = client.post("/api/login", json={
        "email": f"login_{unique_value}@test.com",
        "password": "123456"
    })

    data = login_response.get_json()

    assert login_response.status_code == 200
    assert "access_token" in data
    assert data["user"]["email"] == f"login_{unique_value}@test.com"


def test_get_current_user(client):
    unique_value = str(int(time.time()))

    register_response = client.post("/api/register", json={
        "username": f"meuser_{unique_value}",
        "email": f"me_{unique_value}@test.com",
        "password": "123456",
        "region_id": 1,
        "team_id": 2
    })

    assert register_response.status_code == 201

    login_response = client.post("/api/login", json={
        "email": f"me_{unique_value}@test.com",
        "password": "123456"
    })

    assert login_response.status_code == 200

    token = login_response.get_json()["access_token"]

    me_response = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = me_response.get_json()

    assert me_response.status_code == 200
    assert "user" in data
    assert data["user"]["email"] == f"me_{unique_value}@test.com"
    assert data["user"]["region"] == "APAC"
    assert data["user"]["team"] == "Application Support"