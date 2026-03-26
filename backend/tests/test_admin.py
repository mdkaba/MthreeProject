import time
from db import get_db_connection


def register_user_and_get_token(client, is_admin=False):
    unique_value = str(int(time.time() * 1000))

    email = f"admin_{unique_value}@test.com" if is_admin else f"user_{unique_value}@test.com"
    username = f"adminuser_{unique_value}" if is_admin else f"normaluser_{unique_value}"

    register_response = client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": "123456",
        "region_id": 1,
        "team_id": 2
    })

    assert register_response.status_code == 201

    if is_admin:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET role = 'admin' WHERE email = %s",
            (email,)
        )
        conn.commit()
        cursor.close()
        conn.close()

    login_response = client.post("/api/login", json={
        "email": email,
        "password": "123456"
    })

    assert login_response.status_code == 200
    token = login_response.get_json()["access_token"]

    user_id = login_response.get_json()["user"]["id"]

    return token, user_id, email


def test_admin_can_get_all_users(client):
    admin_token, _, _ = register_user_and_get_token(client, is_admin=True)

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert "users" in data
    assert isinstance(data["users"], list)
    assert len(data["users"]) >= 1


def test_normal_user_cannot_get_all_users(client):
    user_token, _, _ = register_user_and_get_token(client, is_admin=False)

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    data = response.get_json()

    assert response.status_code == 403
    assert data["error"] == "Access denied. Admins only."


def test_admin_can_update_user(client):
    admin_token, _, _ = register_user_and_get_token(client, is_admin=True)
    _, target_user_id, _ = register_user_and_get_token(client, is_admin=False)

    response = client.put(
        f"/api/admin/users/{target_user_id}",
        json={
            "role": "user",
            "region_id": 2,
            "team_id": 3
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "User updated successfully"
    assert data["user"]["id"] == target_user_id
    assert data["user"]["region_id"] == 2
    assert data["user"]["team_id"] == 3
    assert data["user"]["region"] == "EMEA"
    assert data["user"]["team"] == "Incident Management"