# Plan de Pruebas - SIMEL El Tambo (PMV 1 + PMV 2 + PMV 3)

**Fecha de última ejecución local:** 21/11/2026

**Entorno local:** Windows, Python 3.14.7, pytest, coverage 91%

**Entorno remoto:** https://proyecto-licencias.onrender.com (sin cambios en este cierre)

**Resultado local:** 43/43 pruebas PASS (28 unitarias + 15 integración), base de datos aislada

**Resultado remoto:** 9/9 pruebas base PASS y 5/5 pruebas PMV 3 PASS tras el despliegue v3.0.0.

## 1. Ejecución rápida

Para ejecutar todo el plan desde terminal, doble clic en:

```text
EJECUTAR_PRUEBAS.bat
```

O desde PowerShell:

```powershell
.\.venv\Scripts\python.exe .\ejecutar_pruebas.py
```

El script ejecuta la suite local con cobertura, luego las pruebas remotas contra Render y guarda el resultado en `resultados/`. Para las pruebas remotas protegidas, el script toma las credenciales de `SIMEL_REMOTE_USER` y `SIMEL_REMOTE_PASSWORD`; ya no usa contraseñas hardcodeadas ni envía el rol desde el cliente.

Opciones:

```powershell
.\.venv\Scripts\python.exe .\ejecutar_pruebas.py --skip-remote
.\.venv\Scripts\python.exe .\ejecutar_pruebas.py --remote-only
```

## 2. Pruebas locales automatizadas

Comando base:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=src -W ignore -v
```

| ID | Archivo / prueba | Objetivo | Resultado |
|---|---|---|---|
| INT-01 | `test_integracion_endpoint_dashboard_y_bandeja_priorizada` | Dashboard y bandeja priorizada disponibles. | PASS |
| INT-02 | `test_integracion_login_endpoint_jwt` | Login JWT válido e inválido. | PASS |
| INT-03 | `test_integracion_flujo_completo_con_pdf_real_ocr_y_ambos_modelos` | OCR + XGBoost + Random Forest sobre PDF real. | PASS |
| INT-04 | `test_pmv2_endpoints_rag_y_cruce_interfojas` | Indexación RAG y auditoría inter-fojas. | PASS |
| INT-05 | `test_pmv2_carga_masiva_500_transacciones_y_metricas` | Lote de 500 expedientes y métricas consolidadas. | PASS |
| INT-06 | `test_pmv2_listados_router_legacy_y_validaciones_422` | Router legacy, listados y validaciones 422. | PASS |
| INT-07 | `test_pmv3_endpoints_multiagente_hitl_acta_y_alias` | Orquestación StateGraph, HITL, Acta PDF y alias `/agentes` + `/hitl`. | PASS |
| INT-08 | `test_pmv3_metricas_consolidadas_y_validaciones_422` | Métricas PMV 3, SP activos y validaciones 422. Requiere JWT. | PASS |
| INT-09 | `test_pmv3_endpoints_rechazan_peticiones_sin_token` | 401 en orquestar, listar, HITL y Acta PMV 3 (rutas principales y alias). | PASS |
| INT-10 | `test_pmv3_endpoints_rechazan_token_invalido` | 401 ante token JWT inválido. | PASS |
| INT-11 | `test_pmv3_rol_mesa_de_partes_no_puede_orquestar_ni_firmar` | 403 para MESA_DE_PARTES en operaciones; 200 en consultas permitidas. | PASS |
| INT-12 | `test_pmv3_evaluador_puede_orquestar_y_firmar` | 200 con rol EVALUADOR_LICENCIAS. | PASS |
| INT-13 | `test_rutas_pmv1_pmv2_rechazan_acceso_sin_token` | 401 en rutas de negocio PMV 1 y PMV 2. | PASS |
| INT-14 | `test_login_deriva_rol_y_rechaza_rol_solicitado_falso` | El servidor ignora/valida el rol declarado por el cliente. | PASS |
| INT-15 | `test_roles_pmv1_pmv2_consultayoperacion` | Consulta permitida a Mesa de Partes y escritura restringida a Evaluador. | PASS |
| UNIT-01 | `test_hu01_autenticacion_jwt_exitosa_y_bloqueo` | Autenticación JWT y bloqueo de intrusos. | PASS |
| UNIT-02 | `test_hu02_factory_method_y_reglas_sla_dominio` | Factory Method y reglas SLA. | PASS |
| UNIT-03 | `test_hu03_hu04_hu05_caso_uso_aislado_con_mocks` | Caso de uso PMV 1 con mocks. | PASS |
| UNIT-04 | `test_hu06_indexacion_vectorial_chunking_pgvector` | Chunking 500/50, vector 16D y persistencia. | PASS |
| UNIT-05 | `test_hu07_motor_rag_similitud_coseno_zonificacion` | Similitud del coseno y compatibilidad por zona. | PASS |
| UNIT-06 | `test_hu08_auditoria_cruzada_interfojas_dominio_puro` | Discrepancia 110.50 vs 82.00 m² y DNI/RUC. | PASS |
| UNIT-07 | `test_repositorio_hibrido_fallback_local_completo` | Repositorio híbrido en modo `cache_local`. | PASS |
| UNIT-08 | `test_hu08_auditor_interfojas_conforme_y_con_discrepancias` | Cruce conforme y con 3 discrepancias. | PASS |
| UNIT-09 | `test_hu06_hu07_rag_vector_16_dimensiones_y_similitud_coseno` | Vector normalizado y similitud >= 0.88. | PASS |
| UNIT-10 | `test_hu06_indexar_normativa_y_hu07_hu08_auditoria_zonificacion_observada` | Indexación y dictamen observado por zonificación. | PASS |
| UNIT-11 | `test_data_masiva_500_expedientes_metricas_pmv1_y_pmv2` | Lote masivo de 500 y métricas PMV 1 + PMV 2. | PASS |
| UNIT-12 | `test_jwt_configuracion_desde_variables_de_entorno` | JWT firmado con secreto, algoritmo y expiración desde entorno. | PASS |
| UNIT-13 | `test_jwt_falla_sin_secreto_en_produccion` | Fail-fast si falta `JWT_SECRET_KEY` en producción. | PASS |
| UNIT-14 | `test_jwt_valida_horas_de_expiracion` | Rechazo de expiración inválida o menor/igual a cero. | PASS |
| UNIT-15 | `test_jwt_usa_fallback_solo_en_desarrollo` | Secreto efímero únicamente en desarrollo local. | PASS |
| UNIT-16 | `test_pmv3_hu09_grafo_ciclico_conforme_y_observado` | Grafo de 4 nodos, arista cíclica (2 iteraciones), T=0.1 y 0 alucinaciones. | PASS |
| UNIT-17 | `test_pmv3_hu10_validacion_dominio_decision_hitl` | Decisiones HITL válidas, funcionario y sustento obligatorios. | PASS |
| UNIT-18 | `test_pmv3_hu10_generacion_acta_pdf_real_con_cita_legal_y_firma` | Acta PDF real con cita legal, expediente y firma HITL. | PASS |
| UNIT-19 | `test_pmv3_repositorio_hibrido_fallback_local_y_resolucion` | Semillas PMV 3, persistencia local, resolución y métricas. | PASS |
| UNIT-20 | `test_pmv3_casos_de_uso_orquestar_resolver_y_exportar` | Casos de uso PMV 3, síntesis resiliente y exportación PDF. | PASS |
| UNIT-21 | `test_xgboost_importancias_son_reales_globales_y_no_constantes` | Importancias globales reales del modelo XGBoost (suma 1.0) y etiqueta correcta. | PASS |
| UNIT-22 | `test_grafo_no_simula_alucinaciones_ni_llm` | Texto y salidas sin LLM ni alucinaciones simuladas; XAI global y context_precision heurística. | PASS |
| UNIT-23 | `test_mecanismo_persistencia_es_el_real` | Persistencia reportada como UPSERT REST, no SP inexistente. | PASS |
| UNIT-24 | `test_hash_password_verifica_correcta_incorrecta_y_formato_invalido` | PBKDF2-HMAC-SHA256 y comparación segura de hashes. | PASS |
| UNIT-25 | `test_login_rechaza_rol_solicitado_distinto_del_rol_operativo` | Un cliente no puede autoasignarse otro rol. | PASS |
| UNIT-26 | `test_produccion_exige_secretos_y_no_usuarios_demo` | Fail-fast y repositorio Supabase en staging/producción. | PASS |
| UNIT-27 | `test_guardar_predictamen_fallido_revierte_estado` | Fallo HTTP 503 al persistir pre-dictamen revierte caché local. | PASS |
| UNIT-28 | `test_registrar_hitl_fallido_revierte_decision` | Fallo de RPC HITL revierte decisión, firma y archivo local. | PASS |

**Resultado local:** `45 passed`, `1 warning` (deprecación de `starlette.testclient` con `httpx`), cobertura total `91%`.

## 3. Pruebas remotas de humo

| ID | Prueba | Criterio | Resultado |
|---|---|---|---|
| REM-01 | Dashboard `/` | HTTP 200 y contenido `SIMEL`. | PASS |
| REM-02 | OpenAPI `/docs` | HTTP 200. | PASS |
| REM-03 | Bandeja priorizada | `total >= 3` y F1 >= 0.85. | PASS |
| REM-04 | RAG normativas | `total >= 20` y motor pgvector. | PASS |
| REM-05 | Métricas consolidadas | `status=ok`, F1 >= 0.85, context >= 0.94. | PASS |
| REM-06 | Auditoría RAG conforme | Estado `CONFORME_PMV2`. | PASS |
| REM-07 | Indexación vectorial | Vector de 16 dimensiones. | PASS |
| REM-08 | Historial auditorías | `total >= 1`. | PASS |
| REM-09 | Login JWT | Token generado a partir del usuario institucional configurado por entorno. | PASS |
| REM-10 | PMV 3 orquestar LangGraph | `status=success`, iteraciones >= 1, 0 alucinaciones y cita legal 28976/31814. | PASS — `iter=2`, `aluc=0`. |
| REM-11 | PMV 3 listar pre-dictámenes | `total >= 3`. | PASS — `total=5`. |
| REM-12 | PMV 3 resolución HITL | Decisión firmada y `auditoria_inmutable=true`. | PASS — observado y rechazado en BD. |
| REM-13 | PMV 3 Acta PDF | HTTP 200, `application/pdf` y cabecera `%PDF-`. | PASS — 5368 y 5359 bytes. |
| REM-14 | PMV 3 métricas HITL | 5 SP activos, supervisión humana 100%. | PASS — `SP=5`, `PMV3=5`. |

**Resultado remoto base:** `9/9 PASS`. **Resultado remoto PMV 3:** `5/5 PASS`. La verificación se ejecutó con token JWT firmado para `EVALUADOR_LICENCIAS`; el REM con contraseña requiere configurar `SIMEL_REMOTE_USER` y `SIMEL_REMOTE_PASSWORD`.

## 4. Evidencia de la última ejecución

- URL: https://proyecto-licencias.onrender.com
- API Docs: https://proyecto-licencias.onrender.com/docs
- Bandeja: 507 expedientes, F1 XGBoost 0.925.
- RAG: 23+ fragmentos normativos, pgvector HNSW.
- Métricas: `context_precision=0.9998`, fuente `supabase_rpc`.
- Historial de auditorías: más de 2000 registros al momento de la prueba.
- PMV 3 local: 4 agentes deterministas, arista cíclica de refinamiento, T=0.1 como marca de configuración, "0 alucinaciones" reportado como no aplica, Acta PDF con firma HITL y XAI global real de XGBoost.
- Cada ejecución remota agrega/actualiza el fragmento `FRAG-PLAN-PRUEBAS-2026` y una auditoría de prueba.
- La evidencia completa de cada ejecución se guarda en `resultados/resultados_pruebas_AAAAMMDD_HHMMSS.txt`.

## 5. Criterios de aceptación

- 100% de pruebas automatizadas aprobadas.
- Cobertura total >= 90%.
- Endpoints remotos principales responden HTTP 200.
- Flujo RAG + cruce inter-fojas genera dictamen válido.
- Login JWT entrega token utilizable.
- PMV 3: StateGraph multiagente determinista, sin LLM generativo; alucinaciones no aplica.
- PMV 3: endpoints protegidos con JWT y control por rol (401/403).
- PMV 3: XAI global real de XGBoost; `context_precision_rag` marcado como heurística experimental.
- PMV 3: decisión y firma HITL obligatorias antes de la resolución administrativa.
- PMV 3: Acta Resolutiva PDF exportable con cita legal y control SLA.
