import asyncio
import io
import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./cubeai-test.db"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'

from fastapi.testclient import TestClient
import pytest
from PIL import Image
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from apps.api import main
from apps.api.config import settings
from apps.api.db import get_db
from apps.api.db.models import Base, Profile, SolveRecord, User
from apps.api.errors import ScanFailedError
from apps.api.routes import scan as scan_route, ws as ws_route
from apps.api.services.vision import VisionService
from cubeState import CubeState, FACE_TO_COLOR
from cubie import CubieState
from cubieConverter import cubiestate_to_cubestate, cubestate_to_cubiestate
from move import apply_algorithm, apply_algorithm_cubie
from scanSession import CubeScanSession
from scanner import ScanResult
from solver import is_solved


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


def test_coaching_flags_a_sequence_that_does_not_solve_the_state(client):
    response = client.post(
        "/api/coaching",
        json={
            "cube_state": solved_cube_state(),
            "solution_moves": [{"face": "R", "times": 1}],
            "focus": "overall",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "does not solve" in body["explanation"]
    assert any("does not solve" in point for point in body["key_points"])


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


def test_solver_solves_a_real_python_engine_state(client):
    scrambled = apply_algorithm_cubie(CubieState(), "R U F")
    cube_state = {
        "corners": [corner.piece for corner in scrambled.corners],
        "corner_orientations": [
            corner.orientation for corner in scrambled.corners
        ],
        "edges": [edge.piece for edge in scrambled.edges],
        "edge_orientations": [edge.orientation for edge in scrambled.edges],
    }

    response = client.post(
        "/api/solve",
        json={"cube_state": cube_state, "max_moves": 20},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    notation = " ".join(
        move["face"] + {1: "", 2: "2", 3: "'"}[move["times"]]
        for move in body["moves"]
    )
    solved = apply_algorithm_cubie(scrambled, notation)

    assert solved.is_solved()
    assert body["solver_used"] == "kociemba-two-phase"


def test_solver_accepts_frontend_face_grid_and_returns_verified_moves(client):
    solved_cube = CubeState(
        {
            face: [[color] * 3 for _ in range(3)]
            for face, color in FACE_TO_COLOR.items()
        }
    )
    scrambled = apply_algorithm(solved_cube, "R U F")
    face_state = {
        face: [list(row) for row in scrambled.faces[face]]
        for face in ("U", "R", "F", "D", "L", "B")
    }

    response = client.post(
        "/api/solve",
        json={"cube_state": {"faces": face_state}},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    notation = " ".join(
        move["face"] + {1: "", 2: "2", 3: "'"}[move["times"]]
        for move in body["moves"]
    )
    assert is_solved(apply_algorithm(scrambled, notation))


@pytest.mark.parametrize(
    "algorithm",
    ["R", "U", "F", "R U F", "R U R' U' F2 L D"],
)
def test_python_engine_color_cubie_round_trip(algorithm):
    original = apply_algorithm_cubie(CubieState(), algorithm)

    restored = cubestate_to_cubiestate(
        cubiestate_to_cubestate(original)
    )

    assert restored.validate()["valid"]
    assert [corner.to_dict() for corner in restored.corners] == [
        corner.to_dict() for corner in original.corners
    ]
    assert [edge.to_dict() for edge in restored.edges] == [
        edge.to_dict() for edge in original.edges
    ]


def test_sample_photo_uses_real_scanner_and_reports_missing_faces():
    sample_image = (
        Path(__file__).resolve().parents[3] / "test-images" / "cube-color.jpg"
    ).read_bytes()

    with pytest.raises(ScanFailedError) as error:
        asyncio.run(VisionService().scan_image(sample_image))

    assert "U" in error.value.details["scanned_faces"]
    assert set(error.value.details["missing_faces"]) == set("RFDLB")


def test_six_uploaded_faces_build_validate_and_solve(client, monkeypatch):
    faces = {
        "U": "white",
        "R": "red",
        "F": "green",
        "D": "yellow",
        "L": "orange",
        "B": "blue",
    }
    scan_results = [
        ScanResult(
            success=True,
            colors=[[color] * 3 for _ in range(3)],
            stickers=[],
            confidence=0.98,
            face_color=color,
            face_name=face,
        )
        for face, color in faces.items()
    ]

    class FakeScanner:
        def __init__(self):
            self.results = iter(scan_results)

        def scan(self, image):
            return next(self.results)

    service = VisionService()
    session = CubeScanSession(scanner=FakeScanner())
    service.create_scan_session = lambda: session
    monkeypatch.setattr(scan_route, "get_vision_service", lambda: service)

    image_buffer = io.BytesIO()
    Image.new("RGB", (120, 120), "white").save(image_buffer, format="PNG")
    image_data = image_buffer.getvalue()
    
    # Send as JSON payload body where 'files' is explicitly a list of file maps
    payload_files = [
        {
            "filename": f"{face}.png",
            "content": image_data.hex(),
            "content_type": "image/png"
        }
        for face in faces
    ]

    scan_response = client.post("/api/scan/image", json={"files": payload_files})

    assert scan_response.status_code == 200, scan_response.text
    scan_body = scan_response.json()
    assert scan_body["validation"]["valid"] is True
    assert scan_body["metadata"]["detected_faces"] == 6
    assert scan_body["cube_state"] == solved_cube_state()

    solve_response = client.post(
        "/api/solve",
        json={"cube_state": scan_body["cube_state"]},
    )

    assert solve_response.status_code == 200, solve_response.text
    assert solve_response.json()["moves"] == []


def test_websocket_scans_binary_frames_and_completes_validated_cube(client, monkeypatch):
    faces = {
        "U": "white",
        "R": "red",
        "F": "green",
        "D": "yellow",
        "L": "orange",
        "B": "blue",
    }
    scan_results = iter(
        ScanResult(
            success=True,
            colors=[[color] * 3 for _ in range(3)],
            stickers=[],
            confidence=0.99,
            face_color=color,
            face_name=face,
        )
        for face, color in faces.items()
    )

    class FakeScanner:
        def scan(self, image):
            return next(scan_results)

    vision = VisionService()
    vision.create_scan_session = lambda: CubeScanSession(scanner=FakeScanner())
    monkeypatch.setattr(ws_route, "get_vision_service", lambda: vision)
    image_buffer = io.BytesIO()
    Image.new("RGB", (120, 120), "white").save(image_buffer, format="PNG")
    image_bytes = image_buffer.getvalue()

    with client.websocket_connect("/api/scan/session") as websocket:
        assert websocket.receive_json()["type"] == "scan_started"
        progress = websocket.receive_json()
        assert progress["type"] == "progress"
        assert progress["requested_face"] == "U"

        for _ in faces:
            websocket.send_bytes(image_bytes)
            assert websocket.receive_json()["type"] == "progress"
            assert websocket.receive_json()["type"] == "face_detected"

        completed = websocket.receive_json()

    assert completed["type"] == "completed"
    assert completed["validation"]["valid"] is True
    assert completed["cube_state"] == solved_cube_state()
    assert completed["metadata"]["detected_faces"] == 6


def test_websocket_supports_scan_cancellation(client):
    with client.websocket_connect("/api/scan/session") as websocket:
        assert websocket.receive_json()["type"] == "scan_started"
        assert websocket.receive_json()["type"] == "progress"
        websocket.send_json({"type": "cancel"})
        cancelled = websocket.receive_json()

    assert cancelled["type"] == "cancel"
    assert cancelled["reason"] == "User cancelled"


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


def test_guest_profile_solve_history_and_statistics_persist(client):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    main.app.dependency_overrides[get_db] = override_get_db
    try:
        profile_response = client.post("/api/profiles/guest")
        assert profile_response.status_code == 200, profile_response.text
        profile = profile_response.json()

        second_profile_response = client.post("/api/profiles/guest")
        assert second_profile_response.json()["id"] == profile["id"]

        solve_response = client.post(
            "/api/solves",
            json={
                "profile_id": profile["id"],
                "time_ms": 12345,
                "num_moves": 20,
                "scramble": "R U F",
                "solution": "F' U' R'",
                "solver_used": "kociemba-two-phase",
                "penalty_ms": 2000,
            },
        )
        assert solve_response.status_code == 201, solve_response.text

        history_response = client.get(
            "/api/solves",
            params={"profile_id": profile["id"]},
        )
        assert history_response.status_code == 200
        assert len(history_response.json()) == 1
        assert history_response.json()[0]["penalty_ms"] == 2000

        stats_response = client.get(
            f"/api/profiles/{profile['id']}/statistics"
        )
        assert stats_response.status_code == 200
        assert stats_response.json()["total_solves"] == 1
        assert stats_response.json()["best_time_ms"] == 14345

        training_response = client.post(
            "/api/training",
            json={
                "profile_id": profile["id"],
                "algorithm": "R U R' U'",
                "recognition_time_ms": 820,
                "execution_time_ms": 1450,
                "was_correct": True,
            },
        )
        assert training_response.status_code == 201, training_response.text

        training_history = client.get(
            f"/api/profiles/{profile['id']}/training"
        )
        assert training_history.status_code == 200
        assert training_history.json()[0]["recognition_time_ms"] == 820
    finally:
        main.app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_initial_alembic_migration_creates_application_tables(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", database_url)
    repository_root = Path(__file__).resolve().parents[3]

    command.upgrade(Config(str(repository_root / "alembic.ini")), "head")

    migrated_engine = create_engine(database_url)
    try:
        table_names = set(inspect(migrated_engine).get_table_names())
        assert {
            "alembic_version",
            "users",
            "profiles",
            "solve_records",
            "scan_sessions",
            "coaching_records",
            "training_attempts",
        }.issubset(table_names)
    finally:
        migrated_engine.dispose()
