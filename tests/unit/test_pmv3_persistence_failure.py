from dataclasses import asdict

import pytest

from src.adapters.outbound.persistence.supabase_repository_adapter import (
    HybridSupabaseExpedienteRepository,
)


class _RespuestaFallida:
    status_code = 503

    def json(self):
        return {"message": "fallo simulado"}


class _RespuestaExitosa:
    status_code = 201

    def json(self):
        return {"status": "ok"}


@pytest.fixture
def repositorio_remoto(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://proyecto.example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "clave-servicio-de-pruebas")
    monkeypatch.setenv("SIMEL_DB_PATH", str(tmp_path / "bd.json"))
    return HybridSupabaseExpedienteRepository()


def test_guardar_predictamen_fallido_revierte_estado(repositorio_remoto, monkeypatch):
    import src.adapters.outbound.persistence.supabase_repository_adapter as modulo

    monkeypatch.setattr(modulo.httpx, "post", lambda *args, **kwargs: _RespuestaFallida())
    estado_inicial = repositorio_remoto.listar_predictamenes_pmv3()
    predictamen = repositorio_remoto._construir_predictamen_semilla(
        codigo_expediente="EXP-2026-FALLO-PERSISTENCIA",
        decision="PENDIENTE_REVISION_HITL",
        probabilidad=0.5,
        nivel="MEDIO",
        similitud=0.9,
        compatibilidad="COMPATIBLE",
        conforme_interfojas=True,
        discrepancias=0,
        recomendacion="Revisar.",
        dias=1,
    )

    with pytest.raises(RuntimeError, match="HTTP 503"):
        repositorio_remoto.guardar_predictamen_pmv3(predictamen)

    assert repositorio_remoto.listar_predictamenes_pmv3() == estado_inicial


def test_registrar_hitl_fallido_revierte_decision(repositorio_remoto, monkeypatch):
    import src.adapters.outbound.persistence.supabase_repository_adapter as modulo

    monkeypatch.setattr(modulo.httpx, "post", lambda *args, **kwargs: _RespuestaFallida())
    predictamen = repositorio_remoto.obtener_predictamen_pmv3_por_codigo("EXP-2026-0348")
    estado_inicial = asdict(predictamen)
    contenido_inicial = repositorio_remoto._predictamenes_file.read_text(encoding="utf-8")

    with pytest.raises(RuntimeError, match="HTTP 503"):
        repositorio_remoto.registrar_resolucion_hitl_pmv3(
            codigo_expediente="EXP-2026-0348",
            decision="APROBADO_HITL",
            funcionario="funcionario@eltambo.gob.pe",
            observaciones="Decisión de prueba.",
            fecha_iso="2026-11-21T12:00:00+00:00",
        )

    assert asdict(predictamen) == estado_inicial
    assert repositorio_remoto._predictamenes_file.read_text(encoding="utf-8") == contenido_inicial


def test_payload_predictamen_pendiente_usa_fecha_resolucion_nula(repositorio_remoto, monkeypatch):
    import src.adapters.outbound.persistence.supabase_repository_adapter as modulo

    capturado = {}

    def _post(url, **kwargs):
        capturado.update(kwargs.get("json", {}))
        return _RespuestaExitosa()

    monkeypatch.setattr(modulo.httpx, "post", _post)
    predictamen = repositorio_remoto._construir_predictamen_semilla(
        codigo_expediente="EXP-2026-PAYLOAD-NULO",
        decision="PENDIENTE_REVISION_HITL",
        probabilidad=0.5,
        nivel="MEDIO",
        similitud=0.9,
        compatibilidad="COMPATIBLE",
        conforme_interfojas=True,
        discrepancias=0,
        recomendacion="Revisar.",
        dias=1,
    )

    repositorio_remoto.guardar_predictamen_pmv3(predictamen)

    assert capturado["fecha_resolucion_hitl"] is None
