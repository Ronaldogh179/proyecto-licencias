from fastapi.testclient import TestClient

from src.infrastructure.main import app

client = TestClient(app)

PAYLOAD_ORQUESTAR = {
    "codigo_expediente": "EXP-2026-PMV3-SECURITY",
    "giro_comercial": "Bodega",
    "zona_urbana": "CZ",
    "area_declarada_tupa_m2": 45.0,
    "documentos_faltantes": 0,
    "inconsistencias_detectadas": 0,
    "documento_critico_faltante": 0,
}

PAYLOAD_HITL = {
    "codigo_expediente": "EXP-2026-0348",
    "decision_final_humano": "OBSERVADO_HITL",
    "funcionario_evaluador": "evaluador@eltambo.gob.pe",
    "observaciones_funcionario": "Se notifica esquela de subsanación documental.",
}


def _token(correo: str, rol: str) -> str:
    respuesta = client.post(
        "/api/v1/auth/login",
        json={"correo": correo, "password": "municipal2026", "rol": rol},
    )
    assert respuesta.status_code == 200
    return respuesta.json()["data"]["access_token"]


def _headers(correo: str, rol: str) -> dict:
    return {"Authorization": f"Bearer {_token(correo, rol)}"}


def test_pmv3_endpoints_rechazan_peticiones_sin_token():
    assert client.post("/api/v1/pmv3/predictamen/orquestar", json=PAYLOAD_ORQUESTAR).status_code == 401
    assert client.get("/api/v1/pmv3/predictamenes").status_code == 401
    assert client.post("/api/v1/pmv3/hitl/resolver", json=PAYLOAD_HITL).status_code == 401
    assert client.get("/api/v1/pmv3/acta-pdf/EXP-2026-0348").status_code == 401

    assert client.post("/api/v1/agentes/orquestar-predictamen", json=PAYLOAD_ORQUESTAR).status_code == 401
    assert client.get("/api/v1/agentes/predictamenes").status_code == 401
    assert client.post("/api/v1/hitl/resolver-dictamen", json=PAYLOAD_HITL).status_code == 401
    assert client.get("/api/v1/hitl/exportar-acta/EXP-2026-0348").status_code == 401


def test_pmv3_endpoints_rechazan_token_invalido():
    headers = {"Authorization": "Bearer token-invalido"}
    assert client.get("/api/v1/pmv3/predictamenes", headers=headers).status_code == 401
    assert (
        client.post(
            "/api/v1/pmv3/predictamen/orquestar",
            json=PAYLOAD_ORQUESTAR,
            headers=headers,
        ).status_code
        == 401
    )


def test_pmv3_rol_mesa_de_partes_no_puede_orquestar_ni_firmar():
    headers = _headers("mesadepartes@eltambo.gob.pe", "MESA_DE_PARTES")

    assert (
        client.post(
            "/api/v1/pmv3/predictamen/orquestar",
            json=PAYLOAD_ORQUESTAR,
            headers=headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/pmv3/hitl/resolver",
            json=PAYLOAD_HITL,
            headers=headers,
        ).status_code
        == 403
    )
    assert client.get("/api/v1/pmv3/predictamenes", headers=headers).status_code == 200
    assert (
        client.get("/api/v1/pmv3/acta-pdf/EXP-2026-0348", headers=headers).status_code
        == 200
    )


def test_pmv3_evaluador_puede_orquestar_y_firmar():
    headers = _headers("evaluador@eltambo.gob.pe", "EVALUADOR_LICENCIAS")

    res_orquestar = client.post(
        "/api/v1/pmv3/predictamen/orquestar",
        json=PAYLOAD_ORQUESTAR,
        headers=headers,
    )
    assert res_orquestar.status_code == 200

    res_hitl = client.post(
        "/api/v1/pmv3/hitl/resolver",
        json=PAYLOAD_HITL,
        headers=headers,
    )
    assert res_hitl.status_code == 200
    assert res_hitl.json()["predictamen"]["decision_final_humano"] == "OBSERVADO_HITL"
