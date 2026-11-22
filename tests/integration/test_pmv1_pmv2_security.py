from fastapi.testclient import TestClient

from src.infrastructure.main import app

client = TestClient(app)

PASSWORD_DEMO = "municipal2026"


def _headers(correo: str) -> dict:
    respuesta = client.post(
        "/api/v1/auth/login",
        json={"correo": correo, "password": PASSWORD_DEMO},
    )
    assert respuesta.status_code == 200
    return {"Authorization": f"Bearer {respuesta.json()['data']['access_token']}"}


def _payload_indexacion(codigo: str) -> dict:
    return {
        "id_fragmento": codigo,
        "norma_origen": "Ordenanza Municipal N.° 018-2024-MDT/CM",
        "articulo_inciso": "Artículo 12.º, inciso c)",
        "codigo_ciiu": "5610",
        "giro_comercial": "Restaurante",
        "zona_urbana": "RDM",
        "compatibilidad": "COMPATIBLE_CON_RESTRICCION",
        "area_maxima_m2": 80.0,
        "texto_fragmento_chunk": "Fragmento normativo para validación de roles.",
        "tokens_chunk": 500,
        "overlap_tokens": 50,
    }


def test_rutas_pmv1_pmv2_rechazan_acceso_sin_token():
    defensas = [
        ("GET", "/api/v1/expedientes/bandeja", None),
        ("GET", "/api/v1/rag/normativas", None),
        ("GET", "/api/v1/rag/auditorias", None),
        ("GET", "/api/v1/pmv2/auditorias", None),
        ("POST", "/api/v1/expedientes/carga-masiva", {"cantidad": 500}),
        ("POST", "/api/v1/rag/indexar-normativa", _payload_indexacion("FRAG-SIN-TOKEN")),
        ("POST", "/api/v1/pmv2/normativa/indexar", _payload_indexacion("FRAG-SIN-TOKEN-PMV2")),
        ("POST", "/api/v1/pmv2/data-masiva", {"cantidad_transacciones": 500}),
    ]
    for metodo, url, payload in defensas:
        respuesta = client.request(metodo, url, json=payload)
        assert respuesta.status_code == 401, url


def test_login_deriva_rol_y_rechaza_rol_solicitado_falso():
    respuesta = client.post(
        "/api/v1/auth/login",
        json={
            "correo": "mesadepartes@eltambo.gob.pe",
            "password": PASSWORD_DEMO,
        },
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["rol"] == "MESA_DE_PARTES"

    respuesta_falsa = client.post(
        "/api/v1/auth/login",
        json={
            "correo": "evaluador@eltambo.gob.pe",
            "password": PASSWORD_DEMO,
            "rol": "ADMIN_TI",
        },
    )
    assert respuesta_falsa.status_code == 401


def test_roles_pmv1_pmv2_consultayoperacion():
    headers_mesa = _headers("mesadepartes@eltambo.gob.pe")
    headers_evaluador = _headers("evaluador@eltambo.gob.pe")

    for url in (
        "/api/v1/expedientes/bandeja",
        "/api/v1/rag/normativas",
        "/api/v1/rag/auditorias",
        "/api/v1/pmv2/auditorias",
    ):
        assert client.get(url, headers=headers_mesa).status_code == 200

    respuesta_rechazada = client.post(
        "/api/v1/rag/indexar-normativa",
        headers=headers_mesa,
        json=_payload_indexacion("FRAG-MESA-SIN-PERMSO"),
    )
    assert respuesta_rechazada.status_code == 403

    respuesta_permitida = client.post(
        "/api/v1/rag/indexar-normativa",
        headers=headers_evaluador,
        json=_payload_indexacion("FRAG-EVALUADOR-PERMITIDO"),
    )
    assert respuesta_permitida.status_code == 200
