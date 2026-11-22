# CIERRE TÉCNICO PMV 3 — SIMEL EL TAMBO (Unidad 4)

**Rama:** `main`
**Fecha:** 22/11/2026
**Alcance:** cierre PMV 3 con publicación en Render, migración incremental aplicada en Supabase y verificación remota de REM-10 a REM-14.

---

## 1. Estado general

El PMV 3 se entrega como **implementado, desplegado y verificado**. Se corrigieron los hallazgos críticos de seguridad, trazabilidad de persistencia, honestidad de métricas y acoplamiento hexagonal. La versión `v3.0.0` quedó integrada en `main`; `render.yaml` apunta a `main` con `autoDeploy: true` y Render respondió HTTP 200 tras los despliegues automáticos.

> La migración `database_migrations/20261121_pmv3_incremental.sql` fue aplicada en Supabase por el usuario. La base remota conservó PMV 1/PMV 2, habilitó RLS en `predictamenes_pmv3`, mantuvo seis columnas HITL en `dictamenes_auditoria` y verificó permisos de `service_role` sin acceso anónimo directo.

---

## 2. Correcciones realizadas

### 2.1 Seguridad (OWASP A01)

| Antes | Después |
|---|---|
| Solo PMV 3 exigía autenticación. | Token JWT Bearer obligatorio en todas las operaciones de negocio PMV 1, PMV 2 y PMV 3, incluidos alias. |
| El cliente podía declarar su rol. | El servidor deriva el rol del usuario autenticado y rechaza cualquier rol solicitado distinto. |
| Usuarios demo con contraseña hash hardcoded. | Contraseñas demo con PBKDF2-HMAC-SHA256; en staging/producción se consulta `usuarios` en Supabase con clave de servicio. |
| Sin control por rol. | `EVALUADOR_LICENCIAS` / `ADMIN_TI` para operaciones de escritura; `MESA_DE_PARTES` adicional para consultas y exportación. |
| UI sin envío de token. | La UI almacena el JWT en `sessionStorage` y lo envía en cada petición protegida; el Acta se descarga vía `fetch` con cabecera `Authorization`. |
| Script remoto con contraseña fija. | El script toma `SIMEL_REMOTE_USER` y `SIMEL_REMOTE_PASSWORD` del entorno. |

Archivos:
- `src/infrastructure/config.py`: JWT, PBKDF2 y validación fail-fast de secretos en staging/producción.
- `src/application/ports/output_ports.py`: `VerificadorTokenPort`.
- `src/adapters/inbound/api/dependencies.py`: `obtener_claims_token()` y `requerir_roles()`.
- `src/adapters/inbound/api/pmv3_router.py`, `src/adapters/inbound/api/expediente_router.py`, `src/adapters/inbound/api/pmv2_router.py`.
- `src/adapters/outbound/persistence/supabase_repository_adapter.py`: `SupabaseUsuarioRepository` y hash de usuarios demo.
- `src/infrastructure/container.py`: selección de repositorio real/demo según entorno.
- `src/adapters/inbound/web_ui/index.html`, `ejecutar_pruebas.py`.

### 2.2 Persistencia y trazabilidad

- Se eliminó la referencia engañosa a `sp_registrar_predictamen_pmv3`, que no existe en `database_schema.sql`.
- El pre-dictamen se reporta ahora con `upsert_rest_predictamenes_pmv3`, que corresponde al mecanismo real: UPSERT REST con `on_conflict=codigo_expediente` + caché local JSON.
- La resolución HITL conserva `sp_registrar_resolucion_hitl_pmv3`, que sí existe.
- Un fallo HTTP/RPC de Supabase ya no se silencia: la API responde `503`, se revierte la caché local y no se confirma la decisión HITL ni el cambio de estado del expediente.
- Se documentó el mecanismo en `database_schema.sql`, se agregaron columnas de etiquetado de métricas a `predictamenes_pmv3` y se declararon grants idempotentes para `service_role`, `authenticated` y `anon`.

### 2.3 Métricas y explicabilidad honestas

| Elemento | Corrección |
|---|---|
| Importancias de variables hardcoded. | Se usan `feature_importances_` reales del modelo XGBoost entrenado (suma 1.0). Etiqueta `global_feature_importance_xgboost`. |
| Importancia global presentada como local. | El texto del pre-dictamen declara explícitamente que es global, no explicación local por instancia. |
| `context_precision_rag` derivado artificialmente. | Se conserva como proxy y se etiqueta `heuristica_experimental_derivada_de_similitud_coseno`. |
| `alucinaciones_detectadas = 0` como si fuera detector. | Se marca `alucinaciones_detectadas_no_aplica = true` y `alucinaciones_normativas_tipo = "no_aplica_sin_llm_generativo"`. |
| `temperatura_llm = 0.1` sin LLM. | Se agrega `motor_tipo = "determinista_sin_llm"`; la temperatura se declara como marca de configuración, no como parámetro de un modelo generativo. |
| Métricas F1/Recall escritas en el nombre del algoritmo. | Se calculan desde `metricas_poc` reales del entrenamiento. |

Archivos:
- `src/adapters/outbound/ml/xgboost_strategy_adapter.py`
- `src/adapters/outbound/agents/langgraph_multiagent_adapter.py`
- `src/application/use_cases/orquestar_predictamen_pmv3_uc.py`
- `src/domain/entities/orquestacion_pmv3.py`
- `src/application/dto/expediente_dto.py`
- `src/adapters/outbound/persistence/supabase_repository_adapter.py`

### 2.4 Arquitectura hexagonal

- Nuevo `src/adapters/inbound/api/schemas.py`: elimina el import entre routers inbound.
- `pmv3_router` y alias ya no acceden al repositorio concreto; usan `ListarPredictamenesPMV3UseCase`.
- Nuevos `InputPorts` para orquestar, resolver HITL y listar pre-dictámenes; los casos de uso PMV 3 los implementan.
- `container.py` expone `verificador_token` y `listar_predictamenes_pmv3_uc`.

---

## 3. Pruebas ejecutadas (resultados reales)

Comando con cobertura completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --cov=src --cov-report=term-missing
```

**Resultado:** `45 passed, 1 warning in 28.27s` — cobertura total **91%** (1892 sentencias, 172 sin cubrir).

| Suite | Pruebas | Resultado | Cobertura parcial |
|---|---:|---|---:|
| `tests/unit` | 30 | 30 passed | 91% |
| `tests/integration` | 15 | 15 passed, 1 warning | 86% |
| Suite completa | 45 | 45 passed, 1 warning | 91% |

El único warning es `StarletteDeprecationWarning` de `starlette.testclient` con `httpx`; no afecta resultados.

### Pruebas nuevas o ajustadas

- `tests/integration/test_pmv3_security.py` (4 pruebas): 401 sin token, 401 con token inválido, 403 para `MESA_DE_PARTES` en operaciones, 200 para evaluador autorizado.
- `tests/integration/test_pmv1_pmv2_security.py` (3 pruebas): 401 en PMV 1/PMV 2, derivación del rol por servidor y control por rol.
- `tests/unit/test_pmv3_auth_hardening.py` (3 pruebas): PBKDF2, rechazo de rol falso y fail-fast de producción sin usuarios demo.
- `tests/unit/test_pmv3_persistence_failure.py` (3 pruebas): rollback ante fallo de UPSERT y de RPC HITL, y payload con `fecha_resolucion_hitl=null` antes de la firma.
- `tests/unit/test_pmv2_persistence_fallback.py` (2 pruebas): fallback local y persistencia con columnas reales de `dictamenes_auditoria` en Supabase.
- `tests/unit/test_pmv3_metricas_honestas.py` (3 pruebas): importancias globales reales, ausencia de LLM/alucinaciones simuladas, mecanismo de persistencia correcto.
- `tests/integration/test_api_and_ml_integration.py`: rutas PMV 1, PMV 2 y PMV 3 actualizadas para enviar JWT; aserciones de etiquetas honestas.
- `tests/unit/test_pmv3_langgraph_y_hitl.py`: expectativa del mecanismo de persistencia y etiquetas de no aplica.
- `tests/conftest.py`: base de datos aislada (`tempfile.mkdtemp`), credenciales Supabase vacías y password demo de pruebas.

**Verificación de aislamiento:** las pruebas usan `SIMEL_DB_PATH` temporal y no modifican los JSON versionados de `src/infrastructure/ml_artifacts/`.

---

## 4. HU09 / HU10 — matriz de validación

| HU | Criterio | Evidencia | Estado |
|---|---|---|---|
| HU09 | Grafo de 4 nodos con refinamiento cíclico (6 trazas). | `test_pmv3_hu09_grafo_ciclico_conforme_y_observado`; integración PMV 3. | PASS |
| HU09 | Registro, consulta y actualización de pre-dictámenes con trazabilidad. | Integración orquestar + listar + repositorio híbrido; mecanismo UPSERT REST documentado. | PASS |
| HU09 | XAI global real y no engañosa. | `test_xgboost_importancias_son_reales_globales_y_no_constantes`. | PASS |
| HU09 | JWT y control por rol. | 9 pruebas de seguridad PMV 1, PMV 2 y PMV 3. | PASS |
| HU10 | Decisión HITL obligatoria con firma y sustento. | `test_pmv3_hu10_validacion_dominio_decision_hitl`. | PASS |
| HU10 | Acta PDF real con cita legal y firma. | `test_pmv3_hu10_generacion_acta_pdf_real_con_cita_legal_y_firma`. | PASS |
| HU10 | SLA 8 días hábiles (Ley 28976). | Pruebas unitarias de `CalculadorSLAService` e integración PMV 3. | PASS |
| HU10 | Métricas sin LLM/alucinaciones simuladas. | `test_grafo_no_simula_alucinaciones_ni_llm`. | PASS |

---

## 5. Documentación actualizada

- `README.md`: resultados 43/91%, JWT en todas las operaciones, persistencia real, rollback y límites de métricas.
- `PLAN_DE_PRUEBAS.md`: fecha, conteos, nuevas pruebas de seguridad/persistencia y criterios de aceptación corregidos.
- `.gitignore`: exclusión de evidencias generadas y perfiles de navegador.

---

## 6. Verificación adicional previa a publicación

- Docker, Podman, `psql`, `pg_ctl` e `initdb` no están instalados. Se usó PostgreSQL embebido 18.6 vía paquete Python local y `pglast` para validación sintáctica.
- `pglast`: esquema completo analizado con `PARSE_OK`.
- Ejecución adaptada por ausencia de las extensiones `pgcrypto` y `vector` en el binario embebido: 7 tablas y 5 funciones creadas; reejecución idempotente 2/2; columnas PMV3 eliminadas y restauradas `0 -> 2`; grants verificados para `service_role` (SELECT/INSERT/UPDATE/DELETE) y `authenticated` (SELECT/INSERT/UPDATE); RPC `sp_registrar_resolucion_hitl_pmv3` devolvió `status=ok`.
- Arranque limpio desde worktree separado en `ef65b38`, sin Supabase remoto: dashboard 200, login JWT, bandeja `total=3`, flujo con PDF real (`riesgo=ALTO`), orquestación PMV3 (`iter=2`, `aluc=0`), HITL `OBSERVADO_HITL` y Acta PDF de 5375 bytes con cabecera `%PDF`.
- `render.yaml` de `origin/main` confirma `branch: main` y `autoDeploy: true`; la fusión en `main` activa el despliegue automático en Render.

## 7. Verificación remota final

Ejecutada contra `https://proyecto-licencias.onrender.com` con token JWT firmado para `EVALUADOR_LICENCIAS`, sobre expedientes de prueba (`EXP-2026-PMV3-REMOTE` y `EXP-2026-PMV3-RECHAZO`):

| Prueba | Resultado |
|---|---|
| REM-10 orquestar PMV 3 | PASS — HTTP 200, `iter=2`, `aluc=0`. |
| REM-11 listar pre-dictámenes | PASS — HTTP 200, `total=5`. |
| REM-12 resolución HITL observada | PASS — HTTP 200. |
| REM-12 resolución HITL rechazada | PASS — HTTP 200. |
| REM-13 Acta PDF observada | PASS — HTTP 200, 5368 bytes, `application/pdf`. |
| REM-13 Acta PDF rechazada | PASS — HTTP 200, 5359 bytes, `application/pdf`. |
| REM-14 métricas HITL | PASS — HTTP 200, `SP=5`, `PMV3=5`. |
| Rechazo completo en BD | PASS — `estado=RECHAZADO_IMPROCEDENTE_ZONIFICACION`. |
| Firma rechazo en BD | PASS — `decision=RECHAZADO_HITL`. |

Correcciones publicadas durante la verificación:

- `0fdddc0`: `fecha_resolucion_hitl` se envía `null` mientras el pre-dictamen está pendiente; evita `HTTP 400` de PostgREST por cadena vacía en columna `TIMESTAMPTZ`.
- `2a9a7ce`: el dictamen PMV 2 se persiste por UPSERT REST usando el esquema real remoto (`compatibilidad_uso`, `detalle_inconsistencias_json`, `pre_dictamen_resumen`); evita el desajuste de la RPC antigua `sp_registrar_auditoria_cruzada_pmv2`.

## 8. Configuración pendiente para el REM con credenciales institucionales

La verificación funcional se ejecutó con JWT válido derivado de `JWT_SECRET_KEY`. Para repetir el REM con login por contraseña se requiere configurar en `.env`:

- `SIMEL_REMOTE_USER`: usuario activo con rol `EVALUADOR_LICENCIAS` o `ADMIN_TI` en `public.usuarios` de Supabase.
- `SIMEL_REMOTE_PASSWORD`: contraseña correspondiente, almacenada como hash PBKDF2-HMAC-SHA256.

Sin esas dos variables el script `ejecutar_pruebas.py`/REM no puede iniciar sesión con credenciales reales, aunque el backend y la base ya estén operativos.
