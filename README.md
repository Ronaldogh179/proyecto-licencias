# SIMEL - Municipalidad Distrital de El Tambo (PMV 1 y PMV 2)

Sistema web para la evaluación, fiscalización y auditoría documental de licencias de funcionamiento, construido con Arquitectura Hexagonal (Ports & Adapters). Integra el **PMV 1** (OCR con PyMuPDF/Tesseract, modelos XGBoost y Random Forest) y el **PMV 2** (RAG normativo con pgvector, cruce inter-fojas y evaluación documental asistida).

Marco normativo considerado: Ley N.° 28976 (Ley Marco de Licencia de Funcionamiento), Ley N.° 29733 (Protección de Datos Personales) y Ley N.° 31814 (uso de inteligencia artificial).

## 1. Descripción del Proyecto

### PMV 1: evaluación y priorización de expedientes

- Extracción de texto y variables documentales desde PDF con PyMuPDF y Tesseract OCR.
- Predicción del riesgo de observación con XGBoost como modelo principal y Random Forest como respaldo.
- Cálculo de SLA, priorización de la bandeja y persistencia híbrida (Supabase + caché local).
- Autenticación institucional con JWT firmado mediante HMAC-SHA256.

### PMV 2: RAG normativo y auditoría inter-fojas

- Fragmentación y vectorización de normativa municipal/TUPA en vectores de 16 dimensiones.
- Recuperación semántica mediante similitud del coseno y almacenamiento compatible con PostgreSQL + pgvector/HNSW.
- Cruce automático entre formulario TUPA, plano técnico, DNI/RUC, área declarada y dirección del predio.
- Generación de dictámenes explicables con cita legal, nivel de compatibilidad y alertas de discrepancia.
- Procesamiento masivo de 500 a 1000 expedientes y métricas consolidadas PMV 1 + PMV 2.

## 2. Estructura de Arquitectura Hexagonal

La estructura se organiza en las cuatro capas exigidas por la guía, con dependencias dirigidas hacia el dominio:

```text
src/
├── domain/                         # Núcleo puro: no depende de frameworks ni de infraestructura
│   ├── entities/
│   │   ├── expediente.py
│   │   ├── normativa_rag.py
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
│   │   └── pmv2_dto.py
│   ├── ports/
│   │   ├── input_ports.py
│   │   └── output_ports.py
│   └── use_cases/
│       ├── procesar_expediente_uc.py
│       └── auditar_expediente_pmv2_uc.py
│
├── adapters/                       # Implementaciones concretas de los puertos
│   ├── inbound/
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   ├── expediente_router.py
│   │   │   └── pmv2_router.py
│   │   └── web_ui/
│   │       └── index.html
│   └── outbound/
│       ├── ocr/
│       │   └── tesseract_ocr_adapter.py
│       ├── ml/
│       │   └── xgboost_strategy_adapter.py
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

Resultado de referencia:

- 21 pruebas locales aprobadas.
- Cobertura total: 93%.
- 9 pruebas remotas de humo aprobadas.
- Evidencias en `resultados/`.

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
| `GET` | `/api/v1/metricas/consolidado` | Métricas PMV 1 + PMV 2 y stored procedures. |
| `GET` | `/docs` | Documentación interactiva OpenAPI. |

## 7. Seguridad y Buenas Prácticas

- Los secretos se administran exclusivamente por variables de entorno.
- `SUPABASE_SECRET_KEY` y `JWT_SECRET_KEY` no deben exponerse en el frontend ni en Git.
- El dominio permanece aislado de frameworks y librerías de infraestructura.
- Las pruebas de integración y el plan de pruebas remoto permiten validar el despliegue sin hardcodear hosts locales.
