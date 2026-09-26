# SIMEL - Municipalidad Distrital de El Tambo (PMV 1)

Sistema Web con Arquitectura Hibrida Hexagonal (Ports & Adapters) basado en PyMuPDF + Tesseract OCR y Aprendizaje Automatico Supervisado (XGBoost y Random Forest) para la Evaluacion y Fiscalizacion Documental de Licencias de Funcionamiento (Ley N. 28976, Ley N. 29733 y Ley N. 31814).

## 1. Estructura de Capas de la Arquitectura Hexagonal (src/)
- src/domain/: Entidades puras, Objetos de Valor, Servicios de Dominio y patron Factory Method (0% dependencias externas).
- src/application/: Casos de Uso, DTOs, Input Ports y Output Ports con Dependency Injection.
- src/adapters/: Adaptadores Primarios (FastAPI + Web UI) y Secundarios (OCR Adapter, XGBoost/RF Strategy, Supabase Repository).
- src/infrastructure/: Configuracion JWT (HMAC-SHA256), contenedor IoC (container.py), artefactos ML y servidor ASGI (main.py).
- tests/: Suite de pruebas unitarias (tests/unit/) y de integracion (tests/integration/) con PyTest (93% Coverage).
