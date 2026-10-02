import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./cubeai-test.db")

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from apps.api import main
from apps.api.db.models import Base, Profile, SolveRecord, User


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    with TestClient(main.app) as test_client:
        yield test_client


def solved_cube_state():
    return {
        "corners": list(range(8)),
        "corner_orientations": [0] * 8,
        "edges": list(range(12)),
        "edge_orientations": [0] * 12,
    }


def test_health_contract(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"]
    assert response.json()["version"]
    assert response.json()["timestamp"]


def test_validate_solved_cube_contract(client):
    response = client.post(
        "/api/validate",
        json={"cube_state": solved_cube_state()},
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "errors": [],
        "is_solved": True,
        "scramble_distance": 0,
    }


def test_validate_rejects_impossible_permutation(client):
    cube_state = solved_cube_state()
    cube_state["corners"][0], cube_state["corners"][1] = 1, 0

    response = client.post("/api/validate", json={"cube_state": cube_state})

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(error["field"] == "permutation" for error in body["errors"])


def test_solve_response_contract(client):
    response = client.post(
        "/api/solve",
        json={"cube_state": solved_cube_state(), "max_moves": 20},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["num_moves"] == len(body["moves"])
    assert 0 <= body["confidence"] <= 1
    assert body["solving_time_ms"] >= 0
    assert all(move["face"] in "UDFBLR" for move in body["moves"])
    assert all(1 <= move["times"] <= 3 for move in body["moves"])


def test_rejects_malformed_cube_request(client):
    cube_state = solved_cube_state()
    cube_state["corners"] = [0, 1]

    response = client.post("/api/validate", json={"cube_state": cube_state})

    assert response.status_code == 422


def test_solve_record_persists_additional_metadata():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            username="cubist",
            email="cubist@example.com",
            hashed_password="test-hash",
        )
        profile = Profile(name="Test Profile", user=user)
        solve_record = SolveRecord(
            profile=profile,
            time_ms=12000,
            num_moves=20,
            solution="R U R' U'",
            metadata_json={"source": "api-test"},
        )
        session.add(solve_record)
        session.commit()
        loaded_record = session.get(SolveRecord, solve_record.id)

        assert loaded_record is not None
        assert loaded_record.metadata_json == {"source": "api-test"}

    assert "metadata" in SolveRecord.__table__.columns
    engine.dispose()