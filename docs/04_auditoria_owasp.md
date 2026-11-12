# SIMEL — 04 — Auditoría OWASP Top 10:2025

**Curso:** Taller de Proyectos 1 — Semana 13, 12/11/2026.
**Repositorio:** https://github.com/Ronaldogh179/proyecto-licencias
**Código auditado (commit fijo):** `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88`.
**Base:** SIMEL_SEMANA12(4).docx; Guía FURPS+ y OWASP(2).docx; transcripción docente.
**Método:** inspección estática del código por conexión GitHub. No se han ejecutado pruebas dinámicas nuevas ni aplicado remediaciones. El informe de semana 12 (4) fue verificado como ejemplar disponible; no se dispone de la versión (3) para comprobar equivalencia.

## Interpretación de versiones

El Word del docente enumera diez categorías conforme a los nombres y orden de **OWASP 2021**; el ingeniero menciona en clase aplicar la versión **2025**. Para no mezclar categorías, esta evaluación usa la **lista oficial 2025** y conserva una columna de equivalencia temática (no biunívoca) con la guía. Fuente oficial: https://top10.owasp.org/2025/es/ y https://top10.owasp.org/2025/0x00_2025-Introduction/.

## Matriz oficial OWASP 2025 y equivalencia a guía 2021

| Código 2025 | Categoría oficial | Equivalencia orientativa guía | Estado SIMEL |
|---|---|---|---|
| A01:2025 | Pérdida de control de acceso | A01:2021 + SSRF antes A10:2021 | OW-02, OW-03: hallazgo estático |
| A02:2025 | Configuración de seguridad incorrecta | A05:2021 | Pendiente: CORS, debug, secretos, entorno |
| A03:2025 | Fallas en la cadena de suministro de software | A06:2021 ampliada | Sin CVE comprobada; falta SCA/SBOM |
| A04:2025 | Fallas criptográficas | A02:2021 | OW-01: verificación de contraseña |
| A05:2025 | Inyección | A03:2021 | No evaluado mediante pruebas |
| A06:2025 | Diseño inseguro | A04:2021 | OW-03 y FU-01: revisión de diseño |
| A07:2025 | Fallas de autenticación | A07:2021 | OW-01: fallo verificable por lectura de código |
| A08:2025 | Fallas en la integridad del software o de los datos | A08:2021 | Pendiente: CI, artefactos y procedencia |
| A09:2025 | Fallas de registro, alertas y monitoreo de seguridad | A09:2021 | FU-02: excepción silenciada |
| A10:2025 | Manejo inadecuado de condiciones excepcionales | Categoría nueva 2025 | FU-01, FU-02: fallback y except pass |

La categoría A03:2025 amplía el análisis de componentes vulnerables a la cadena de suministro; SSRF fue incorporado en A01:2025 y A10:2025 aborda manejo inadecuado de condiciones excepcionales. No evaluado **no** significa seguro ni conforme.

## Hallazgos confirmados por lectura de código y pendientes de prueba

### OW-01 — Verificación de contraseña sin cotejo de hash

- **Severidad preliminar:** Crítica; **referencia:** A07:2025, A04:2025.
- **Evidencia:** [src/infrastructure/config.py:L45-L47](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/infrastructure/config.py#L45). verificar_password() comprueba solo que password tenga >=4 caracteres y exista password_hash; no compara ambos.
- **Riesgo:** Un usuario existente podría autenticarse con una clave incorrecta.
- **Plan:** Sustituir por verificación real de hash resistente (Argon2/bcrypt), migrar fixture de credenciales y evitar fallback.
- **Prueba de aceptación pendiente:** Login correcto 200; contraseña incorrecta 401; usuario inexistente 401.
- **Responsable propuesto:** Backend + QA. **Estado de implementación:** pendiente; no se presume corregido.

### OW-02 — Rutas PMV1 y PMV2 sin dependencia explícita de JWT

- **Severidad preliminar:** Crítica; **referencia:** A01:2025.
- **Evidencia:** [src/adapters/inbound/api/pmv2_router.py:L47-L66](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/inbound/api/pmv2_router.py#L47). Los handlers de indexación y auditoría inspeccionados no declaran dependencia de autorización, situación análoga en el router PMV1.
- **Riesgo:** Posibles operaciones sin identidad ni permisos verificados; requiere comprobación HTTP.
- **Plan:** Dependencia centralizada de autenticación/autorización con permisos mínimos y rutas protegidas.
- **Prueba de aceptación pendiente:** Sin JWT 401, token inválido 401, rol insuficiente 403, funcionario válido 2xx.
- **Responsable propuesto:** Integración + QA. **Estado de implementación:** pendiente; no se presume corregido.

### OW-03 — Rol controlado por el cliente llega al JWT

- **Severidad preliminar:** Alta; **referencia:** A01:2025, A06:2025.
- **Evidencia:** [src/application/use_cases/procesar_expediente_uc.py:L22-L39](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/application/use_cases/procesar_expediente_uc.py#L22). Se usa rol=rol or usuario.rol_operativo al generar el token, y LoginRequest acepta rol enviado por el cliente.
- **Riesgo:** Un usuario podría emitir un JWT con rol mayor al registrado; impacto pendiente de test.
- **Plan:** Tomar rol únicamente del registro autorizado del usuario; probar escalamiento.
- **Prueba de aceptación pendiente:** Solicitar rol no permitido: token refleja rol almacenado o solicitud es rechazada.
- **Responsable propuesto:** Backend + QA. **Estado de implementación:** pendiente; no se presume corregido.

### FU-01 — Fallback engañoso ante errores de extracción PDF

- **Severidad preliminar:** Alta; **referencia:** A10:2025, A06:2025.
- **Evidencia:** [src/adapters/outbound/ocr/tesseract_ocr_adapter.py:L16-L26; L58](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/ocr/tesseract_ocr_adapter.py#L16). Except genérico asigna texto descriptivo como si fuera extraído; confianza_ocr es constante 96.8.
- **Riesgo:** Errores de documentos pueden pasar inadvertidos y afectar el resultado ML.
- **Plan:** Señalar PDF corrupto/escaneado/sin texto y resultado verificable; no atribuir confianza ficticia.
- **Prueba de aceptación pendiente:** PDF digital, escaneado, corrupto y sin adjunto: salida diferenciada.
- **Responsable propuesto:** Backend/ML + QA. **Estado de implementación:** pendiente; no se presume corregido.

### FU-02 — Sincronización remota oculta fallos

- **Severidad preliminar:** Alta; **referencia:** A09:2025, A10:2025.
- **Evidencia:** [src/adapters/outbound/persistence/supabase_repository_adapter.py:L114-L138](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/persistence/supabase_repository_adapter.py#L114). Las solicitudes httpx.post no validan status_code y las excepciones se silencian con pass.
- **Riesgo:** Podría confundirse persistencia local con remota exitosa.
- **Plan:** Comprobar estado de respuesta, registro seguro, estado de sincronización y reintentos controlados.
- **Prueba de aceptación pendiente:** Mock de 401, 500, timeout, desconexión y reconciliación de registros.
- **Responsable propuesto:** Integración + QA. **Estado de implementación:** pendiente; no se presume corregido.

### FU-03 — Lectura completa de PDF sin límite declarado

- **Severidad preliminar:** Media; **referencia:** A06:2025, A10:2025.
- **Evidencia:** [src/adapters/inbound/api/expediente_router.py:L31-L50](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/inbound/api/expediente_router.py#L31). El handler ejecuta await archivo_pdf.read() sin tamaño máximo explícito.
- **Riesgo:** Posible presión sobre memoria con archivos grandes, si no existe límite de infraestructura.
- **Plan:** Límites de tamaño, tipo MIME validado y error 413/422 controlado.
- **Prueba de aceptación pendiente:** Archivos debajo/encima del límite, corruptos y formato no válido.
- **Responsable propuesto:** Integración + QA. **Estado de implementación:** pendiente; no se presume corregido.

## Severidad, impacto y cobertura

Severidades **cualitativas preliminares**: OW-01 y OW-02 crítica; OW-03, FU-01, FU-02 alta; FU-03 media. Las consecuencias potenciales se describen por hallazgo, pero no se ha realizado una evaluación cuantitativa de probabilidad, explotación controlada, escaneo de dependencias ni análisis dinámico. Por ello no corresponde declarar un score OWASP global ni emitir cumplimiento.

**Procedencia:** enlace a código inmutable en cada ficha. Extractos visuales del ZIP verificados por conexión GitHub, no screenshots literales del navegador. Las diez categorías de la guía de 2021 siguen cubiertas por equivalencia.
