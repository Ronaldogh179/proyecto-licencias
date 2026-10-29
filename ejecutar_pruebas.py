#!/usr/bin/env python3
"""Ejecuta el plan de pruebas local y remoto de SIMEL El Tambo."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "resultados"
DEFAULT_BASE_URL = "https://proyecto-licencias.onrender.com"
HTTP_TIMEOUT = 180


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def emit(self, text: str = "") -> None:
        print(text)
        self.lines.append(str(text))

    def save(self) -> Path:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        path = RESULTS_DIR / f"resultados_pruebas_{datetime.now():%Y%m%d_%H%M%S}.txt"
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return path


def _get_text(url: str, timeout: int = HTTP_TIMEOUT, attempts: int = 4) -> tuple[int, str]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={"Accept": "text/html,application/json"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code >= 500 and attempt + 1 < attempts:
                time.sleep(10)
                continue
            raise
        except Exception as error:  # noqa: BLE001
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(10)
                continue
            raise

    raise last_error or RuntimeError("Error de conexiÃ³n desconocido")


def _request_json(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    timeout: int = HTTP_TIMEOUT,
) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    last_error: Exception | None = None
    attempts = 4 if method == "GET" else 1
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return response.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"HTTP {error.code}: {body[:300]}")
            if method == "GET" and error.code >= 500 and attempt + 1 < attempts:
                time.sleep(10)
                continue
            raise last_error from error
        except Exception as error:  # noqa: BLE001
            last_error = error
            if method == "GET" and attempt + 1 < attempts:
                time.sleep(10)
                continue
            raise

    raise last_error or RuntimeError("Error de conexiÃ³n desconocido")


def run_local(report: Report) -> bool:
    report.emit("=" * 86)
    report.emit("1. SUITE LOCAL: PYTEST + COBERTURA")
    report.emit("=" * 86)
    report.emit("Comando: python -m pytest --cov=src -W ignore -v")
    report.emit("")

    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=src",
        "-W",
        "ignore",
        "-v",
    ]
    process = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    output = (process.stdout or "") + (process.stderr or "")
    report.emit(output.rstrip())

    coverage_match = re.search(r"^TOTAL\s+\d+\s+\d+\s+(\d+)%", output, flags=re.MULTILINE)
    coverage = coverage_match.group(1) if coverage_match else "no detectada"
    ok = process.returncode == 0
    report.emit("")
    report.emit(f"RESULTADO LOCAL: {'PASS' if ok else 'FAIL'} | Cobertura: {coverage}%")
    report.emit("")
    return ok


def run_remote(report: Report, base_url: str) -> bool:
    report.emit("=" * 86)
    report.emit("2. PRUEBAS REMOTAS DE HUMO: RENDER")
    report.emit("=" * 86)
    report.emit(f"URL: {base_url}")
    report.emit("")
    report.emit(f"{'ESTADO':<7} | {'PRUEBA':<34} | DETALLE")
    report.emit("-" * 86)

    results: list[bool] = []

    def check(name: str, action) -> None:
        try:
            ok, detail = action()
        except Exception as error:  # noqa: BLE001
            ok, detail = False, str(error)
        report.emit(f"{'PASS' if ok else 'FAIL':<7} | {name:<34} | {detail}")
        results.append(ok)

    def dashboard():
        status, html = _get_text(f"{base_url}/")
        return status == 200 and "SIMEL" in html, f"HTTP {status}, {len(html)} bytes"

    def docs():
        status, _ = _get_text(f"{base_url}/docs")
        return status == 200, f"HTTP {status}"

    def bandeja():
        status, data = _request_json(f"{base_url}/api/v1/expedientes/bandeja")
        total = int(data.get("total", 0))
        f1 = float(data.get("metricas_modelos_poc", {}).get("xgboost", {}).get("f1_test", 0))
        return status == 200 and total >= 3 and f1 >= 0.85, f"total={total}, F1={f1}"

    def normativas():
        status, data = _request_json(f"{base_url}/api/v1/rag/normativas")
        total = int(data.get("total", 0))
        motor = str(data.get("motor_vectorial", ""))
        return status == 200 and total >= 20 and "pgvector" in motor, f"total={total}, motor={motor}"

    def metricas():
        status, data = _request_json(f"{base_url}/api/v1/metricas/consolidado")
        f1 = float(data.get("pmv1_ml", {}).get("f1_score", 0))
        context = float(data.get("pmv2_rag", {}).get("context_precision", 0))
        return (
            status == 200
            and data.get("status") == "ok"
            and f1 >= 0.85
            and context >= 0.94,
            f"F1={f1}, context={context}, fuente={data.get('fuente')}",
        )

    def auditoria():
        payload = {
            "codigo_expediente": "EXP-2026-0350",
            "giro_comercial": "Bodega",
            "zona_urbana": "CZ",
            "dni_ruc_formulario": "10728491023",
            "dni_ruc_plano_dni": "10728491023",
            "area_formulario_m2": 42.0,
            "area_plano_m2": 42.0,
            "direccion_formulario": "Jr. Arequipa N.Â° 890 - El Tambo",
            "direccion_plano": "Jr. Arequipa N.Â° 890 - El Tambo",
        }
        status, data = _request_json(
            f"{base_url}/api/v1/rag/auditar-expediente",
            method="POST",
            payload=payload,
        )
        auditoria_data = data.get("auditoria", {})
        return (
            status == 200
            and data.get("status") == "ok"
            and auditoria_data.get("estado_auditoria_pmv2") == "CONFORME_PMV2",
            f"estado={auditoria_data.get('estado_auditoria_pmv2')}, sim={auditoria_data.get('similitud_coseno_rag')}",
        )

    def indexacion():
        payload = {
            "id_fragmento": "FRAG-PLAN-PRUEBAS-2026",
            "norma_origen": "Ordenanza Municipal N.Â° 018-2024-MDT/CM",
            "articulo_inciso": "Plan de pruebas",
            "codigo_ciiu": "5610",
            "giro_comercial": "Restaurante",
            "zona_urbana": "RDM",
            "compatibilidad": "COMPATIBLE_CON_RESTRICCION",
            "area_maxima_m2": 80.0,
            "texto_fragmento_chunk": "Fragmento remoto de verificacion del plan de pruebas.",
            "tokens_chunk": 500,
            "overlap_tokens": 50,
        }
        status, data = _request_json(
            f"{base_url}/api/v1/rag/indexar-normativa",
            method="POST",
            payload=payload,
        )
        return (
            status == 200
            and data.get("status") == "ok"
            and int(data.get("dimensiones_vector", 0)) == 16,
            f"dimensiones={data.get('dimensiones_vector')}, id={data.get('fragmento', {}).get('id_fragmento')}",
        )

    def historial():
        status, data = _request_json(f"{base_url}/api/v1/rag/auditorias")
        total = int(data.get("total", 0))
        return status == 200 and total >= 1, f"total={total}"

    def login():
        payload = {
            "correo": "evaluador@eltambo.gob.pe",
            "password": "municipal2026",
            "rol": "EVALUADOR_LICENCIAS",
        }
        status, data = _request_json(
            f"{base_url}/api/v1/auth/login",
            method="POST",
            payload=payload,
        )
        token = str(data.get("data", {}).get("access_token", ""))
        return status == 200 and len(token) > 20, f"rol={data.get('data', {}).get('rol')}"

    check("Dashboard /", dashboard)
    check("OpenAPI /docs", docs)
    check("Bandeja priorizada", bandeja)
    check("RAG normativas", normativas)
    check("Metricas consolidadas", metricas)
    check("Auditoria RAG conforme", auditoria)
    check("Indexacion vectorial", indexacion)
    check("Historial auditorias", historial)
    check("Login JWT", login)

    ok = all(results)
    report.emit("")
    report.emit(f"RESULTADO REMOTO: {'PASS' if ok else 'FAIL'} ({sum(results)}/{len(results)})")
    report.emit("")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan de pruebas SIMEL El Tambo")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="URL del backend en Render")
    parser.add_argument("--skip-remote", action="store_true", help="Ejecutar solo pruebas locales")
    parser.add_argument("--remote-only", action="store_true", help="Ejecutar solo pruebas remotas")
    args = parser.parse_args()

    report = Report()
    report.emit("=" * 86)
    report.emit("PLAN DE PRUEBAS SIMEL EL TAMBO - PMV 1 + PMV 2")
    report.emit(f"Fecha: {datetime.now():%d/%m/%Y %H:%M:%S}")
    report.emit("=" * 86)
    report.emit("")

    local_ok = True
    remote_ok = True
    if not args.remote_only:
        local_ok = run_local(report)
    if not args.skip_remote:
        remote_ok = run_remote(report, args.base_url.rstrip("/"))

    overall = local_ok and remote_ok
    report.emit("=" * 86)
    report.emit(f"RESULTADO GENERAL: {'PASS' if overall else 'FAIL'}")
    report.emit("=" * 86)

    path = report.save()
    report.emit(f"Evidencia guardada en: {path}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
