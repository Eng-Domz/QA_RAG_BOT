from fastapi.testclient import TestClient

from api.main import API_VERSION, APP_NAME, APP_VERSION, create_app


def test_health_reports_process_is_alive():
    with TestClient(create_app()) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_ready_after_startup():
    with TestClient(create_app()) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_typed_503_when_a_dependency_is_unavailable():
    with TestClient(create_app(readiness_check=lambda: False)) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_readiness_does_not_leak_dependency_exceptions():
    def failing_check() -> bool:
        raise RuntimeError("database password must not be exposed")

    with TestClient(create_app(readiness_check=failing_check)) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert "database password" not in response.text


def test_version_exposes_stable_application_metadata():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json() == {
        "name": APP_NAME,
        "version": APP_VERSION,
        "api_version": API_VERSION,
    }


def test_openapi_schema_documents_operational_endpoints():
    with TestClient(create_app()) as client:
        docs_response = client.get("/docs")
        schema_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert schema_response.status_code == 200
    assert {"/healthz", "/readyz", "/api/v1/version"} <= set(
        schema_response.json()["paths"]
    )
