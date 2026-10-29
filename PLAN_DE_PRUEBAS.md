# Plan de Pruebas - SIMEL El Tambo (PMV 1 + PMV 2)

**Fecha de última ejecución:** 29/10/2026  
**Entorno local:** Windows, Python 3.14.7, pytest 9.1.1, coverage 93%  
**Entorno remoto:** https://proyecto-licencias.onrender.com  
**Resultado general:** 21/21 pruebas locales PASS - 9/9 pruebas remotas PASS

## 1. Ejecución rápida

Para ejecutar todo el plan desde terminal, doble clic en:

```text
EJECUTAR_PRUEBAS.bat
```

O desde PowerShell:

```powershell
.\.venv\Scripts\python.exe .\ejecutar_pruebas.py
```

El script ejecuta la suite local con cobertura, luego las pruebas remotas contra Render y guarda el resultado en `resultados/`.

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

**Resultado local:** `21 passed`, `0 warnings`, cobertura total `93%`.

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
| REM-09 | Login JWT | Token generado con rol `EVALUADOR_LICENCIAS`. | PASS |

**Resultado remoto:** `9/9 PASS`.

## 4. Evidencia de la última ejecución

- URL: https://proyecto-licencias.onrender.com
- API Docs: https://proyecto-licencias.onrender.com/docs
- Bandeja: 507 expedientes, F1 XGBoost 0.925.
- RAG: 23+ fragmentos normativos, pgvector HNSW.
- Métricas: `context_precision=0.9998`, fuente `supabase_rpc`.
- Historial de auditorías: más de 2000 registros al momento de la prueba.
- Cada ejecución remota agrega/actualiza el fragmento `FRAG-PLAN-PRUEBAS-2026` y una auditoría de prueba.
- La evidencia completa de cada ejecución se guarda en `resultados/resultados_pruebas_AAAAMMDD_HHMMSS.txt`.

## 5. Criterios de aceptación

- 100% de pruebas automatizadas aprobadas.
- Cobertura total >= 92%.
- 0 warnings en la ejecución con `-W ignore`.
- Endpoints remotos principales responden HTTP 200.
- Flujo RAG + cruce inter-fojas genera dictamen válido.
- Login JWT entrega token utilizable.
