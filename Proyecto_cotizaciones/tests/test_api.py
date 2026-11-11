from collections.abc import Iterator
from datetime import date, timedelta
from uuid import uuid4

import mongomock
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        mongo_uri=SecretStr("mongodb://localhost/test"),
        mongo_database="hostech_test",
        cors_origins="http://testserver",
    )
    application = create_app(
        settings,
        mongo_client_factory=mongomock.MongoClient,
    )
    with TestClient(application) as test_client:
        yield test_client


def quote_document(
    *,
    document_id: str | None = None,
    destination: str = "Riviera Maya - MX",
    category: str = "5EST",
    nightly_rate: float = 1250.0,
    timestamp: str = "2026-11-09T12:00:00+00:00",
) -> dict:
    check_in = date(2026, 12, 12)
    nights = 2
    room_total = nightly_rate * nights
    return {
        "metadata_extraccion": {
            "id_documento": document_id or str(uuid4()),
            "timestamp": timestamp,
            "proveedor": "Hostech (datos simulados)",
            "tipo_dato": "SIMULADO_NO_REAL",
            "es_simulado": True,
        },
        "parametros_busqueda": {
            "destino": destination,
            "nacionalidad": "México",
            "fechas": {
                "check_in": check_in.isoformat(),
                "check_out": (check_in + timedelta(days=nights)).isoformat(),
                "noches": nights,
            },
            "ocupacion": {
                "habitaciones": 1,
                "adultos": 2,
                "menores": 0,
            },
            "total_hoteles_disponibles": 200,
        },
        "resultados": [
            {
                "hotel_nombre": f"Hotel Costa {category}",
                "categoria": category,
                "ubicacion": destination.split(" - ")[0],
                "tarifa_promedio_noche": nightly_rate,
                "costo_total_estancia": room_total,
                "moneda": "MXN",
                "opciones_habitacion": [
                    {
                        "tipo_habitacion": "Doble Standard",
                        "plan_alimento": "Sólo Habitación",
                        "costo_total": room_total,
                        "moneda": "MXN",
                        "estado_disponibilidad": "confirmado",
                        "politicas": {
                            "fecha_limite_pago": "2026-12-01",
                            "cargos_cancelacion": "Tarifa no reembolsable.",
                            "cargos_no_show": "Penalidad simulada.",
                        },
                    }
                ],
            }
        ],
    }


def test_health_checks_database(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"
    assert response.json()["collection"] == "Proyecto"


def test_cors_rejects_wildcard_origin() -> None:
    with pytest.raises(ValidationError):
        Settings(
            mongo_uri=SecretStr("mongodb://localhost/test"),
            mongo_database="hostech_test",
            cors_origins="*",
        )


def test_create_valid_quote_and_get_by_natural_key(client: TestClient) -> None:
    payload = quote_document()
    response = client.post("/api/v1/cotizaciones", json=payload)

    assert response.status_code == 201
    assert response.json()["metadata_extraccion"]["id_documento"] == (
        payload["metadata_extraccion"]["id_documento"]
    )
    assert response.json()["metadata_extraccion"]["es_simulado"] is True

    get_response = client.get(
        f"/api/v1/cotizaciones/{payload['metadata_extraccion']['id_documento']}"
    )
    assert get_response.status_code == 200
    assert get_response.json() == response.json()


def test_reject_invalid_quote(client: TestClient) -> None:
    payload = quote_document()
    payload["metadata_extraccion"]["es_simulado"] = False

    response = client.post("/api/v1/cotizaciones", json=payload)

    assert response.status_code == 422


def test_reject_duplicate_natural_key(client: TestClient) -> None:
    payload = quote_document()
    first = client.post("/api/v1/cotizaciones", json=payload)
    duplicate = client.post("/api/v1/cotizaciones", json=payload)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert "id_documento" in duplicate.json()["detail"]


def test_list_quotes_with_pagination_and_filters(client: TestClient) -> None:
    first = quote_document(destination="Riviera Maya - MX")
    second = quote_document(destination="Cancún - MX")
    client.post("/api/v1/cotizaciones", json=first)
    client.post("/api/v1/cotizaciones", json=second)

    response = client.get(
        "/api/v1/cotizaciones",
        params={"destino": "Riviera Maya - MX", "limit": 1, "offset": 0},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert (
        response.json()["items"][0]["parametros_busqueda"]["destino"]
        == "Riviera Maya - MX"
    )


def test_replace_quote_and_prevent_natural_key_change(client: TestClient) -> None:
    original = quote_document()
    document_id = original["metadata_extraccion"]["id_documento"]
    assert client.post("/api/v1/cotizaciones", json=original).status_code == 201

    changed = quote_document(
        document_id=document_id,
        destination="Cancún - MX",
        nightly_rate=1700.0,
    )
    updated = client.put(f"/api/v1/cotizaciones/{document_id}", json=changed)
    assert updated.status_code == 200
    assert updated.json()["resultados"][0]["tarifa_promedio_noche"] == 1700.0

    mismatch = quote_document(destination="Cancún - MX")
    rejected = client.put(f"/api/v1/cotizaciones/{document_id}", json=mismatch)
    assert rejected.status_code == 422


def test_delete_quote(client: TestClient) -> None:
    payload = quote_document()
    document_id = payload["metadata_extraccion"]["id_documento"]
    client.post("/api/v1/cotizaciones", json=payload)

    deleted = client.delete(f"/api/v1/cotizaciones/{document_id}")
    missing = client.get(f"/api/v1/cotizaciones/{document_id}")

    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_average_rate_analysis_uses_aggregation(client: TestClient) -> None:
    client.post(
        "/api/v1/cotizaciones",
        json=quote_document(nightly_rate=1000.0, category="3EST"),
    )
    client.post(
        "/api/v1/cotizaciones",
        json=quote_document(nightly_rate=2000.0, category="5EST"),
    )

    response = client.get("/api/v1/analytics/tarifa-promedio-por-destino")

    assert response.status_code == 200
    assert response.json() == [
        {
            "destino": "Riviera Maya - MX",
            "tarifa_promedio_noche": 1500.0,
            "total_hoteles": 2,
        }
    ]


def test_cheapest_hotels_can_filter_by_star_category(client: TestClient) -> None:
    client.post(
        "/api/v1/cotizaciones",
        json=quote_document(nightly_rate=700.0, category="3EST"),
    )
    client.post(
        "/api/v1/cotizaciones",
        json=quote_document(nightly_rate=1800.0, category="5EST"),
    )

    response = client.get(
        "/api/v1/analytics/hoteles-mas-economicos",
        params={"categoria": "5EST", "limit": 5},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["categoria"] == "5EST"
    assert response.json()[0]["tarifa_promedio_noche"] == 1800.0


def test_quote_count_by_month_analysis(client: TestClient) -> None:
    for timestamp in (
        "2026-11-01T10:00:00+00:00",
        "2026-11-15T10:00:00+00:00",
        "2026-12-01T10:00:00+00:00",
    ):
        client.post(
            "/api/v1/cotizaciones",
            json=quote_document(timestamp=timestamp),
        )

    response = client.get("/api/v1/analytics/cotizaciones-por-mes")

    assert response.status_code == 200
    assert response.json() == [
        {"mes": "2026-11", "total_cotizaciones": 2},
        {"mes": "2026-12", "total_cotizaciones": 1},
    ]
