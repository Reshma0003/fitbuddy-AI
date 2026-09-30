import os


os.environ["GEMINI_API_KEY"] = "test-key"

os.environ["ADMIN_TOKEN"] = "test-admin"


from fastapi.testclient import TestClient

from app.main import app

from app import routes


client = TestClient(app)


def fake_workout(data):

    return """
Day 1: Full Body

Day 2: Cardio

Day 3: Upper Body

Day 4: Rest

Day 5: Lower Body

Day 6: Core

Day 7: Recovery
"""


def fake_tip(data):

    return (
        "Stay hydrated and include "
        "protein-rich foods in balanced meals."
    )


def fake_update(
    original,
    data,
    feedback
):

    return (
        original
        + f"\n\nUpdated from feedback: {feedback}"
    )


def test_home_page():

    response = client.get("/")

    assert response.status_code == 200

    assert "FitBuddy" in response.text


def test_health():

    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200

    assert (
        response.json()["gemini_configured"]
        is True
    )


def test_generate_and_store(
    monkeypatch
):

    monkeypatch.setattr(
        routes,
        "generate_workout_gemini",
        fake_workout
    )

    monkeypatch.setattr(
        routes,
        "generate_nutrition_tip_with_flash",
        fake_tip
    )


    response = client.post(

        "/api/generate-workout",

        json={

            "name": "Test User",

            "user_id": "test001",

            "age": 21,

            "weight": 60,

            "goal": "muscle gain",

            "intensity": "medium",
        },
    )


    assert response.status_code == 200


    body = response.json()


    assert body["plan_id"] > 0


    assert "Day 1" in body["workout_plan"]


def test_feedback_updates_plan(
    monkeypatch
):

    monkeypatch.setattr(
        routes,
        "generate_workout_gemini",
        fake_workout
    )

    monkeypatch.setattr(
        routes,
        "generate_nutrition_tip_with_flash",
        fake_tip
    )

    monkeypatch.setattr(
        routes,
        "update_workout_plan",
        fake_update
    )


    client.post(

        "/api/generate-workout",

        json={

            "name": "Feedback User",

            "user_id": "feedback001",

            "age": 25,

            "weight": 70,

            "goal": "general wellness",

            "intensity": "low",
        },
    )


    response = client.post(

        "/api/submit-feedback",

        json={

            "user_id": "feedback001",

            "feedback": "Add yoga.",
        },
    )


    assert response.status_code == 200


    assert (
        "Add yoga."
        in response.json()["updated_plan"]
    )


def test_admin_requires_token():

    response = client.get(
        "/view-all-users"
    )

    assert response.status_code == 401


    response = client.get(
        "/view-all-users?token=test-admin"
    )

    assert response.status_code == 200