# CIERRE TÉCNICO PMV 3 — SIMEL EL TAMBO (Unidad 4)

**Rama:** `fix/cierre-pmv3-unidad4`
**Fecha:** 21/11/2026
**Alcance:** corrección de hallazgos de la auditoría PMV 3 sin push, merge, despliegue ni modificación de datos/DDL productivos.

---

## 1. Estado general

El PMV 3 se entrega como **implementado y verificado localmente**. Se corrigieron los hallazgos críticos de seguridad, trazabilidad de persistencia, honestidad de métricas y acoplamiento hexagonal. La versión `v3.0.0` **no ha sido desplegada**: `render.yaml` sigue apuntando a `main` con `autoDeploy: true`; el cierre queda confirmado solo en un commit local de esta rama.

> No se ejecutaron migraciones ni RPC contra Supabase. Los cambios SQL son exclusivamente al archivo `database_schema.sql` y requieren validación en una base PostgreSQL desechable. Docker y `psql` no están disponibles en el entorno de cierre.

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

**Resultado:** `43 passed, 1 warning in 28.07s` — cobertura total **91%** (1880 sentencias, 163 sin cubrir).

| Suite | Pruebas | Resultado | Cobertura parcial |
|---|---:|---|---:|
| `tests/unit` | 28 | 28 passed | 91% |
| `tests/integration` | 15 | 15 passed, 1 warning | 86% |
| Suite completa | 43 | 43 passed, 1 warning | 91% |

El único warning es `StarletteDeprecationWarning` de `starlette.testclient` con `httpx`; no afecta resultados.

### Pruebas nuevas o ajustadas

- `tests/integration/test_pmv3_security.py` (4 pruebas): 401 sin token, 401 con token inválido, 403 para `MESA_DE_PARTES` en operaciones, 200 para evaluador autorizado.
- `tests/integration/test_pmv1_pmv2_security.py` (3 pruebas): 401 en PMV 1/PMV 2, derivación del rol por servidor y control por rol.
- `tests/unit/test_pmv3_auth_hardening.py` (3 pruebas): PBKDF2, rechazo de rol falso y fail-fast de producción sin usuarios demo.
- `tests/unit/test_pmv3_persistence_failure.py` (2 pruebas): rollback ante fallo de UPSERT y de RPC HITL.
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

## 6. Pendiente

1. Validar `database_schema.sql` en una base PostgreSQL desechable: aplicación limpia, upgrade, idempotencia, UPSERT de `predictamenes_pmv3`, RPC HITL y grants. No ejecutado aquí por ausencia de Docker/psql.
2. Desplegar `v3.0.0` a `main`/Render para ejecutar REM-10 a REM-14 (pendientes).
3. Ejecutar pruebas remotas con `SIMEL_REMOTE_USER` y `SIMEL_REMOTE_PASSWORD`; el script ya envía JWT pero no modifica Supabase de prueba.
4. Completar evidencias de prueba de usuario/actas de validación académica si la rúbrica «forbs y el otro» las exige; no se encontró ese documento en el repositorio.
