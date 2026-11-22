# SIMEL — Sistema Inteligente de Licencias de Funcionamiento

### Municipalidad Distrital de El Tambo · Arquitectura Hexagonal · Versión 3.0.0

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-PDF-EF3939)](https://pymupdf.readthedocs.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-FF6600)](https://xgboost.readthedocs.io/)
[![pytest](https://img.shields.io/badge/pytest-61%20passed-0A9EDC?logo=pytest&logoColor=white)](PLAN_DE_PRUEBAS.md)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)](PLAN_DE_PRUEBAS.md)
[![Version](https://img.shields.io/badge/version-3.0.0-blue)](README.md)

Plataforma web para la evaluación, fiscalización y auditoría documental de licencias de funcionamiento. Integra **OCR + Machine Learning (PMV 1)**, **RAG normativo con pgvector (PMV 2)** y **orquestación multiagente con Human-in-the-Loop (PMV 3)** sobre una arquitectura hexagonal estricta.

## Acceso rápido

| Recurso | Enlace |
|---|---|
| **Aplicación en producción** | **[https://proyecto-licencias.onrender.com](https://proyecto-licencias.onrender.com)** |
| Documentación interactiva (Swagger UI) | [https://proyecto-licencias.onrender.com/docs](https://proyecto-licencias.onrender.com/docs) |
| Repositorio GitHub | [https://github.com/Ronaldogh179/proyecto-licencias](https://github.com/Ronaldogh179/proyecto-licencias) |
| Más proyectos del autor | [https://github.com/Ronaldogh179?tab=repositories](https://github.com/Ronaldogh179?tab=repositories) |
| Plan de pruebas y evidencias | [PLAN_DE_PRUEBAS.md](PLAN_DE_PRUEBAS.md) |
| Esquema de base de datos | [database_schema.sql](database_schema.sql) |
| Configuración de ejemplo | [.env.example](.env.example) |

> El servicio está desplegado en Render (plan free). La primera petición puede tardar unos segundos mientras se reactiva el contenedor.

## Estado del proyecto

| Componente | Alcance | Estado |
|---|---|---|
| PMV 1 | OCR, XGBoost/Random Forest, SLA y bandeja priorizada. | Completado |
| PMV 2 | RAG normativo pgvector, cruce inter-fojas y dictámenes explicables. | Completado |
| PMV 3 | StateGraph multiagente, supervisión HITL, SLA y Acta Resolutiva PDF. | Completado |
| Calidad | 61 pruebas locales aisladas (41 unitarias + 20 de integración), cobertura 91% y 5 procedimientos almacenados declarados. | Completado |

## Stack tecnológico

| Capa | Tecnologías |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| IA / ML | XGBoost, Random Forest, scikit-learn |
| OCR / PDF | PyMuPDF, Tesseract OCR |
| RAG | pgvector, similitud del coseno, vectores de 16 dimensiones |
| Persistencia | Supabase PostgreSQL + caché local de respaldo |
| Seguridad | JWT HMAC-SHA256 y variables de entorno |
| Pruebas | pytest, coverage, pruebas unitarias y de integración |

Marco normativo considerado: Ley N.° 28976 (Ley Marco de Licencia de Funcionamiento), Ley N.° 29733 (Protección de Datos Personales) y Ley N.° 31814 (uso de inteligencia artificial).

## Flujo de uso

1. Ingresa a la aplicación y autentícate con JWT institucional.
2. Registra o carga un expediente TUPA con su PDF.
3. El motor OCR extrae variables y los modelos ML estiman el riesgo de observación.
4. El motor RAG recupera la normativa aplicable y ejecuta el cruce inter-fojas.
5. El StateGraph multiagente genera el pre-dictamen explicable con cita legal.
6. El funcionario revisa el pre-dictamen y registra su decisión y firma (HITL).
7. Descarga el Acta Resolutiva PDF con control SLA y trazabilidad completa.

## 1. Descripción del Proyecto

### PMV 1: evaluación y priorización de expedientes

- Extracción de texto y variables documentales desde PDF con PyMuPDF y Tesseract OCR.
- Predicción del riesgo de observación con XGBoost como modelo principal y Random Forest como respaldo.
- Cálculo de SLA, priorización de la bandeja y persistencia híbrida (Supabase + caché local).
- Autenticación institucional con JWT firmado mediante HMAC-SHA256.
- OCR híbrido: PyMuPDF extrae texto nativo y Tesseract procesa las páginas escaneadas. El formulario ofrece modo automático (indicadores estimados desde el PDF, sujetos a revisión) o manual (respeta los valores del evaluador) y valida PDF vacíos, dañados o protegidos con contraseña.

### PMV 2: RAG normativo y auditoría inter-fojas

- Fragmentación y vectorización de normativa municipal/TUPA en vectores de 16 dimensiones.
- Recuperación semántica mediante similitud del coseno y almacenamiento compatible con PostgreSQL + pgvector/HNSW.
- Cruce automático entre formulario TUPA, plano técnico, DNI/RUC, área declarada y dirección del predio.
- Generación de dictámenes explicables con cita legal, nivel de compatibilidad y alertas de discrepancia.
- Procesamiento masivo de 500 a 1000 expedientes y métricas consolidadas PMV 1 + PMV 2.

### PMV 3: orquestación multiagente y gobernanza HITL

- StateGraph determinista de 4 agentes (OCR, XGBoost, RAG normativo y Supervisor Auditor) sobre un estado compartido tipado.
- Arista condicional cíclica con máximo 2 iteraciones para refinamiento normativo cuando la similitud es baja, existe discrepancia inter-fojas, exceso de área, incompatibilidad de zonificación o riesgo alto.
- Temperatura `0.1`, `0` alucinaciones normativas y pre-dictamen explicable con cita legal consolidada.
- Supervisión humana obligatoria (Human-in-the-Loop, Ley N.° 31814): la IA recomienda y el funcionario decide y firma.
- Control SLA de 8 días hábiles (Ley N.° 28976) con semáforo de cumplimiento.
- Generación de Acta Resolutiva PDF en memoria con PyMuPDF, membrete municipal, cita legal y firma HITL.

## 2. Estructura de Arquitectura Hexagonal

La estructura se organiza en las cuatro capas exigidas por la guía, con dependencias dirigidas hacia el dominio:

```text
src/
├── domain/                         # Núcleo puro: no depende de frameworks ni de infraestructura
│   ├── entities/
│   │   ├── expediente.py
│   │   ├── normativa_rag.py
│   │   ├── orquestacion_pmv3.py
│   │   └── usuario.py
│   ├── value_objects/
│   │   └── nivel_riesgo.py
│   ├── services/
│   │   ├── auditor_interfojas_service.py
│   │   └── calculador_sla.py
│   └── factories/
│       └── expediente_factory.py
│
├── application/                    # Casos de uso, DTOs y contratos de entrada/salida
│   ├── dto/
│   │   ├── expediente_dto.py
│   │   ├── pmv2_dto.py
│   │   └── pmv3_dto.py
│   ├── ports/
│   │   ├── input_ports.py
│   │   └── output_ports.py
│   └── use_cases/
│       ├── procesar_expediente_uc.py
│       ├── auditar_expediente_pmv2_uc.py
│       └── orquestar_predictamen_pmv3_uc.py
│
├── adapters/                       # Implementaciones concretas de los puertos
│   ├── inbound/
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   ├── expediente_router.py
│   │   │   ├── pmv2_router.py
│   │   │   └── pmv3_router.py
│   │   └── web_ui/
│   │       └── index.html
│   └── outbound/
│       ├── ocr/
│       │   └── tesseract_ocr_adapter.py
│       ├── ml/
│       │   └── xgboost_strategy_adapter.py
│       ├── agents/
│       │   └── langgraph_multiagent_adapter.py
│       ├── pdf/
│       │   └── pymupdf_acta_generator_adapter.py
│       ├── persistence/
│       │   └── supabase_repository_adapter.py
│       └── rag/
│           └── pgvector_rag_adapter.py
│
└── infrastructure/                 # Composición, configuración y servidor FastAPI
    ├── config.py
    ├── container.py
    ├── main.py
    ├── generar_artefactos.py
    └── ml_artifacts/
```

### Rol de cada capa

| Capa | Responsabilidad | Dependencias permitidas |
|---|---|---|
| `domain` | Entidades, value objects, reglas de negocio, servicios puros y Factory Method. | Solo biblioteca estándar y módulos de `src.domain`. No importa FastAPI, Pydantic, SQL, Supabase, OCR ni ML. |
| `application` | Casos de uso, DTOs y puertos de entrada/salida. Orquesta el dominio sin conocer detalles técnicos. | `src.domain` y contratos propios de `src.application`. No importa adaptadores ni infraestructura. |
| `adapters` | Controladores HTTP, UI, OCR, modelos ML, persistencia Supabase y motor RAG pgvector. Implementan los puertos. | `src.application`, `src.domain` y librerías técnicas de cada adaptador. |
| `infrastructure` | Servidor FastAPI, configuración por variables de entorno, contenedor IoC y artefactos locales de respaldo. | Adaptadores, aplicación, dominio y librerías de infraestructura. Es el punto de composición. |

**Dirección de dependencias:** `infrastructure -> adapters -> application -> domain`.

El contenedor IoC se publica en `app.state.container` desde `main.py`. Los routers lo obtienen mediante `dependencies.py`, evitando que la capa `adapters` importe directamente `infrastructure`.

La auditoría confirma que `domain` no contiene imports de FastAPI, Pydantic, Supabase, httpx, scikit-learn, XGBoost, PyMuPDF ni Tesseract. Los archivos de `ml_artifacts` son datos de respaldo para demo/pruebas y no forman parte del dominio.

## 3. Despliegue en Entorno Cloud (Staging / No Localhost)

### Principio de configuración

- Ninguna conexión a Supabase, base de datos o servicio externo usa `localhost` ni `127.0.0.1` en `src/`.
- `SUPABASE_URL` y las claves se leen con `os.getenv` desde variables de entorno.
- `JWT_SECRET_KEY`, algoritmo y expiración se leen desde variables de entorno.
- En `staging`/`production`, la aplicación falla al iniciar sesión si `JWT_SECRET_KEY` no está configurada.
- El único uso de `0.0.0.0` está en el `Dockerfile` como dirección de escucha interna del contenedor; no es una dependencia de red local.

### Docker

El `Dockerfile` usa `python:3.11-slim`, instala Tesseract OCR con idioma español y arranca Uvicorn con el puerto inyectado por la plataforma:

```dockerfile
CMD ["sh", "-c", "uvicorn src.infrastructure.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Construcción y ejecución local del contenedor:

```powershell
docker build -t simel-eltambo .
docker run --env-file .env -p 8000:8000 simel-eltambo
```

### Render

El archivo `render.yaml` define un servicio web Docker con health check en `/`:

- Runtime: Docker.
- Plan: free.
- Región: Oregon.
- Rama: `main`.
- Auto-deploy: habilitado.
- Variables sensibles: configuradas manualmente en el panel de Render (`sync: false`).

Servicio desplegado de referencia:

- Aplicación: https://proyecto-licencias.onrender.com
- Documentación OpenAPI: https://proyecto-licencias.onrender.com/docs

Pasos de despliegue:

1. Conectar el repositorio de GitHub a Render.
2. Crear el servicio usando el blueprint `render.yaml`.
3. Registrar las variables de entorno indicadas en la tabla siguiente.
4. Verificar el health check `GET /` y la documentación `GET /docs`.
5. Confirmar que `GET /api/v1/rag/normativas` responda con `motor_vectorial = pgvector HNSW`.

> El plan free de Render suspende el servicio por inactividad. La primera petición puede tardar mientras el contenedor se reactiva.

### Vercel

`pyproject.toml` declara el entrypoint ASGI para Vercel:

```toml
[tool.vercel]
entrypoint = "src.infrastructure.main:app"
```

Vercel puede usarse para publicar la interfaz o como capa de entrada serverless. Para este proyecto se recomienda mantener el backend con OCR, XGBoost y procesamiento masivo en Render, y usar Vercel solo para frontend o proxy cuando corresponda. Las variables de entorno deben configurarse también en el panel de Vercel; no se deben incluir secretos en el repositorio.

### Supabase

La persistencia remota usa Supabase PostgreSQL con la extensión `pgvector` y los procedimientos almacenados definidos en `database_schema.sql`:

- `sp_indexar_fragmento_normativo`
- `sp_validar_zonificacion_rag_coseno`
- `sp_registrar_auditoria_cruzada_pmv2`
- `sp_obtener_metricas_pmv1_pmv2`
- `sp_registrar_resolucion_hitl_pmv3`

El pre-dictamen multiagente se persiste en la tabla `predictamenes_pmv3` mediante un UPSERT REST con `on_conflict=codigo_expediente` y caché local JSON. No existe `sp_registrar_predictamen_pmv3`; la resolución HITL sí se registra mediante `sp_registrar_resolucion_hitl_pmv3`.

La aplicación mantiene un caché local de respaldo para demo y pruebas, pero la conexión cloud se activa únicamente cuando `SUPABASE_URL` y la clave están presentes.

### Variables de Entorno

| Variable | Requerida | Valor / Ejemplo | Uso |
|---|---|---|---|
| `ENVIRONMENT` | Recomendada | `production` en Render; `development` local | Activa validaciones de seguridad para staging/producción. |
| `SUPABASE_URL` | Sí | `https://<proyecto>.supabase.co` | URL remota de Supabase. Nunca usar localhost. |
| `SUPABASE_KEY` | Sí | Clave anónima o service role | Autenticación REST contra Supabase. |
| `SUPABASE_SECRET_KEY` | Recomendada | Service role key | Clave prioritaria para operaciones de backend. No exponerla en frontend. |
| `JWT_SECRET_KEY` | Sí | Secreto largo y aleatorio | Firma de tokens JWT. Obligatoria en staging/producción. |
| `JWT_ALGORITHM` | Opcional | `HS256` | Algoritmo de firma JWT. |
| `JWT_EXPIRATION_HOURS` | Opcional | `8` | Vigencia del token en horas. |
| `PORT` | Inyectada por Render | `8000` | Puerto interno del contenedor. Render la define automáticamente. |

Plantilla disponible en `.env.example`. El archivo `.env` real está excluido por `.gitignore` y nunca debe subirse al repositorio.

## 4. Ejecución Local

### Requisitos

- Python 3.11 o superior.
- Tesseract OCR con idioma español para el flujo OCR real.
- Docker (opcional) para ejecutar el contenedor de producción.
- Variables de entorno configuradas según la sección anterior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.infrastructure.main:app --reload
```

Abrir la URL local indicada por Uvicorn, normalmente `http://127.0.0.1:8000`. Esta dirección es solo para desarrollo; la configuración cloud no depende de ella.

## 5. Pruebas

El proyecto incluye pruebas unitarias y de integración:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=src -W ignore -v
```

También se puede ejecutar el plan completo con doble clic en `EJECUTAR_PRUEBAS.bat`, que corre la suite local y las pruebas remotas de humo contra Render. El detalle de casos y resultados está en `PLAN_DE_PRUEBAS.md`.

Resultado verificado en `main`:

- 61 pruebas locales aprobadas (41 unitarias + 20 de integración), ejecutadas con base de datos aislada.
- Cobertura total: 91% (`pytest --cov=src`).
- 9 pruebas remotas base aprobadas y 5 pruebas PMV 3 aprobadas tras el despliegue v3.0.0.
- Detalle y resultados finales en `CIERRE_TECNICO_PMV3.md` y `PLAN_DE_PRUEBAS.md`.

## 6. Endpoints Principales

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Autenticación JWT institucional. |
| `POST` | `/api/v1/expedientes/evaluar` | Ingesta PDF, OCR, predicción ML y persistencia. |
| `GET` | `/api/v1/expedientes/bandeja` | Bandeja priorizada por riesgo. |
| `POST` | `/api/v1/rag/indexar-normativa` | Fragmentar, vectorizar e indexar normativa. |
| `GET` | `/api/v1/rag/normativas` | Listar fragmentos normativos vectorizados. |
| `POST` | `/api/v1/rag/auditar-expediente` | RAG de zonificación y cruce inter-fojas. |
| `GET` | `/api/v1/rag/auditorias` | Historial de auditorías PMV 2. |
| `POST` | `/api/v1/expedientes/carga-masiva` | Procesamiento masivo de 500 a 1000 expedientes. |
| `GET` | `/api/v1/metricas/consolidado` | Métricas PMV 1 + PMV 2 + PMV 3 y stored procedures. |
| `POST` | `/api/v1/pmv3/predictamen/orquestar` | Ejecutar StateGraph multiagente y registrar pre-dictamen. Requiere JWT de evaluador. |
| `GET` | `/api/v1/pmv3/predictamenes` | Listar pre-dictámenes PMV 3 con trazas y estado SLA/HITL. |
| `POST` | `/api/v1/pmv3/hitl/resolver` | Registrar decisión y firma obligatoria del funcionario. |
| `GET` | `/api/v1/pmv3/acta-pdf/{codigo_expediente}` | Exportar Acta Resolutiva PDF con firma HITL. |
| `GET` | `/docs` | Documentación interactiva OpenAPI. |

## 7. Seguridad y Buenas Prácticas

- Los secretos se administran exclusivamente por variables de entorno.
- `SUPABASE_SECRET_KEY` y `JWT_SECRET_KEY` no deben exponerse en el frontend ni en Git.
- El dominio permanece aislado de frameworks y librerías de infraestructura.
- Las pruebas de integración y el plan de pruebas remoto permiten validar el despliegue sin hardcodear hosts locales.
- Todas las operaciones de negocio PMV 1, PMV 2 y PMV 3 exigen JWT Bearer; las operaciones de escritura requieren `EVALUADOR_LICENCIAS` o `ADMIN_TI` y las consultas permiten también a `MESA_DE_PARTES`.
- En staging/producción los funcionarios se leen de `usuarios` en Supabase; los usuarios demo solo existen en desarrollo/pruebas. Las contraseñas se verifican con PBKDF2-HMAC-SHA256.
- Si falla la persistencia PMV 3 en Supabase, la API responde `503`, revierte el estado local y no confirma la decisión HITL.
- `database_migrations/20261121_pmv3_incremental.sql` fue aplicado en Supabase y verificado: RLS activo, seis columnas HITL en `dictamenes_auditoria`, permisos de `service_role` y sin acceso directo anónimo.
- En el PMV 3, la IA solo recomienda: la decisión final y la firma son siempre del funcionario evaluador (Ley N.° 31814).
- El motor multiagente es determinista y no usa LLM generativo; "temperatura 0.1" y "0 alucinaciones" se reportan como marcas de configuración/no aplica, no como métricas medidas.
- La importancia de variables es global (`feature_importance` de XGBoost), no una explicación local por instancia; `context_precision_rag` es una heurística experimental derivada de la similitud coseno.
- El Acta Resolutiva PDF se genera en memoria y no deja archivos temporales en el servidor.

## 8. Créditos y Enlaces

Proyecto desarrollado para la **Municipalidad Distrital de El Tambo**, Huancayo, Perú.

- Aplicación: [https://proyecto-licencias.onrender.com](https://proyecto-licencias.onrender.com)
- Documentación API: [https://proyecto-licencias.onrender.com/docs](https://proyecto-licencias.onrender.com/docs)
- Repositorio: [https://github.com/Ronaldogh179/proyecto-licencias](https://github.com/Ronaldogh179/proyecto-licencias)
- Más proyectos: [https://github.com/Ronaldogh179?tab=repositories](https://github.com/Ronaldogh179?tab=repositories)
