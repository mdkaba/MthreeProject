import time


def register_and_login(client):
    unique_value = str(int(time.time() * 1000))

    register_response = client.post("/api/register", json={
        "username": f"taskuser_{unique_value}",
        "email": f"task_{unique_value}@test.com",
        "password": "123456",
        "region_id": 1,
        "team_id": 2
    })

    assert register_response.status_code == 201

    login_response = client.post("/api/login", json={
        "email": f"task_{unique_value}@test.com",
        "password": "123456"
    })

    assert login_response.status_code == 200

    token = login_response.get_json()["access_token"]
    return token


def test_create_task(client):
    token = register_and_login(client)

    response = client.post(
        "/api/tasks",
        json={
            "task_name": "Training Session",
            "task_date": "2026-04-15",
            "category": "Study",
            "hours": 1.30,
            "description": "Backend testing task"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["task"]["task_name"] == "Training Session"
    assert data["task"]["category"] == "Study"
    assert data["task"]["hours_stored"] == 1.5


def test_get_tasks(client):
    token = register_and_login(client)

    create_response = client.post(
        "/api/tasks",
        json={
            "task_name": "Interview Prep",
            "task_date": "2026-04-20",
            "category": "Interview",
            "hours": 1.5,
            "description": "Prepare interview"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert "tasks" in data
    assert len(data["tasks"]) >= 1
    assert data["tasks"][0]["category"] is not None


def test_task_summary(client):
    token = register_and_login(client)

    task_1 = client.post(
        "/api/tasks",
        json={
            "task_name": "Study Session 1",
            "task_date": "2026-04-10",
            "category": "Study",
            "hours": 1.0,
            "description": "Study work"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    task_2 = client.post(
        "/api/tasks",
        json={
            "task_name": "Study Session 2",
            "task_date": "2026-04-11",
            "category": "Study",
            "hours": 1.5,
            "description": "More study work"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert task_1.status_code == 201
    assert task_2.status_code == 201

    response = client.get(
        "/api/tasks/summary?month=2026-04",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["month"] == "2026-04"
    assert "activities" in data
    assert "grand_total" in data
    assert data["grand_total"]["total_count"] >= 2

    activity_names = [activity["activity"] for activity in data["activities"]]
    assert "Study" in activity_names
    assert data["grand_total"]["total_count"] >= 2