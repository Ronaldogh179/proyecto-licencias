# Proyecto SIMEL — Taller de Proyectos 1 / Semana 13

Repositorio: https://github.com/Ronaldogh179/proyecto-licencias
Instantánea auditada: `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` (rama `main`, corte de código revisado y confirmado 12/11/2026).
Base documental: `SIMEL_SEMANA12(4).docx`, `Guia FURPS+ y OWASP(2).docx` y transcripción de clase.
Fecha documental: 12/11/2026.
**Alcance:** inspección estática de código GitHub en commit inmutable y resultados históricos diferenciados. Se actualizaron únicamente documentos de auditoría; no se modificó código ejecutable ni se realizaron pruebas dinámicas nuevas. La publicación de los Markdown en GitHub es documental, no remediación.

**Aclaración documental:** se revisó el ejemplar proporcionado `SIMEL_SEMANA12(4).docx`. No se dispone del archivo `(3)` para acreditar que sea idéntico. Las cifras históricas solo se atribuyen al informe consultado.

# 05 — Plan de remediación OWASP

**Objetivo:** mitigar primero autenticación, autorización y elevación de rol, sin alterar el flujo válido de HU01–HU08.

## Acciones priorizadas
### OW-01 — La verificación de contraseña no coteja el hash
**Componente:** src/infrastructure/config.py (líneas 45–47) · **Prioridad preliminar:** Crítica para autenticación · **Factor:** Seguridad / F

**Evidencia de código:** verificar_password() devuelve len(password_plano.strip()) >= 4 and bool(password_hash); no usa bcrypt/argon2 ni otro algoritmo comparativo.

**Riesgo:** Un usuario existente podría recibir un token con cualquier contraseña de cuatro o más caracteres, pendiente de prueba controlada.

**Comprobación requerida:** Cuenta autorizada con contraseña correcta = 200; contraseña incorrecta de >=4 caracteres = 401; usuario inexistente = 401.

**Recomendación:** Implementar un verificador de hashes real; migrar credenciales de demostración a hashes válidos.

**Estado de implementación:** no aplicado en esta auditoría; resultado dinámico pendiente.

**Enlace:** https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/infrastructure/config.py#L45

### OW-02 — Rutas de operaciones sin dependencias de autorización
**Componente:** src/adapters/inbound/api/expediente_router.py y pmv2_router.py (líneas 31–87 y 47–109) · **Prioridad preliminar:** Crítica para control de acceso · **Factor:** Seguridad / F

**Evidencia de código:** Los handlers examinados no declaran Depends() de verificación de token o roles; main.py solo incorpora los routers.

**Riesgo:** Acceso potencial a registros, indexación o auditoría sin una identidad validada, sujeto a verificación HTTP.

**Comprobación requerida:** Sin token 401; token inválido o vencido 401; rol insuficiente 403; usuario legítimo conserva respuestas 2xx.

**Recomendación:** Agregar dependencia reutilizable que valide firma, expiración y permisos; aplicar en rutas privadas de ambos PMV.

**Estado de implementación:** no aplicado en esta auditoría; resultado dinámico pendiente.

**Enlaces:** https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/inbound/api/expediente_router.py#L31-L49 y https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/inbound/api/pmv2_router.py#L47-L66

### OW-03 — El rol proporcionado por el cliente se incorpora al token
**Componente:** src/application/use_cases/procesar_expediente_uc.py (líneas 22–38) · **Prioridad preliminar:** Alta · **Factor:** Seguridad / F

**Evidencia de código:** El caso de uso pasa rol=rol or usuario.rol_operativo al generador JWT; el LoginRequest permite indicar rol.

**Riesgo:** Un usuario con cuenta podría solicitar un rol distinto al registrado; el impacto requiere validación al incorporar autorización.

**Comprobación requerida:** Solicitar rol de mayor privilegio y verificar que el token refleje solo el rol real o se rechace.

**Recomendación:** Derivar claims de rol únicamente del repositorio de usuarios y comprobar la autorización efectiva.

**Estado de implementación:** no aplicado en esta auditoría; resultado dinámico pendiente.

**Enlace:** https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/application/use_cases/procesar_expediente_uc.py#L22

### FU-01 — Manejo de excepciones en PDF y estado de extracción (seguimiento transversal)

- **Identificador único:** FU-01. Clasificación principal: **FURPS+ / Reliability**; vinculación complementaria, sin duplicar el hallazgo, con **OWASP A10:2025 (Manejo inadecuado de condiciones excepcionales)** y A06:2025 cuando corresponda al diseño.
- **PMV:** 1 (extractor PDF); impacto posterior sobre datos usados para la clasificación y trazabilidad.
- **Severidad preliminar:** Alta para fiabilidad de la evaluación documental; no existe prueba de explotación de seguridad.
- **Hecho comprobado:** `pymupdf.open` y `get_text('text')` están dentro de un `try`; ante una excepción se asigna texto sustituto (`except Exception`) y `confianza_ocr=96.8` se fija sin cálculo empírico. Los PDF escaneados pueden carecer de capa textual.
- **Fuente inmutable:** [adaptador PyMuPDF, líneas 16–26](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/ocr/tesseract_ocr_adapter.py#L16-L26) y [confianza fija, líneas 53–59](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/ocr/tesseract_ocr_adapter.py#L53-L59).
- **Acción de corrección futura:** distinguir PDF digital válido, PDF sin texto, PDF escaneado, PDF malformado y extracción fallida; devolver estado y error trazables; impedir que texto sintético de respaldo o una confianza fija se presente como extracción satisfactoria. No introducir OCR no verificado como función disponible.
- **Pruebas de aceptación pendientes:** (P1) PDF digital legible → texto real y estado éxito; (P2) PDF corrupto → respuesta/estado de error controlado, sin texto inventado; (P3) PDF escaneado sin capa textual → resultado sin texto identificado y derivación/revisión manual; (P4) PDF digital vacío → salida vacía y advertencia; (P5) excepción forzada de extracción → registro sin datos sensibles, sin clasificar sobre datos ficticios; (P6) ausencia de adjunto → comportamiento contractual documentado.
- **Evidencia futura de cierre:** commit de remediación, ejecución `pytest` con casos P1–P6, prueba de integración para PMV 1, evidencia de ausencia de regresión, captura literal del código y resultados (cuando estén disponibles).
- **Estado al 12/11/2026:** **pendiente de implementación y validación**. No existe un resultado nuevo de ejecución con el que acreditar cierre.


### FU-02 — Sincronización remota sin verificar resultado ni registrar fallo
**Componente:** src/adapters/outbound/persistence/supabase_repository_adapter.py (líneas 114–139) · **Prioridad preliminar:** Alta para trazabilidad · **Factor:** R / S

**Evidencia de código:** Las llamadas httpx.post no comprueban status_code; los except Exception hacen pass silencioso.

**Riesgo:** La copia local puede aparentar sincronización exitosa sin evidencia de persistencia remota.

**Comprobación requerida:** Simular 401, 500, timeout y corte de red; verificar alertas, respuesta de la API y consistencia.

**Recomendación:** Validar respuesta HTTP; registrar fallos sin exponer datos personales o secretos; señalar estado local/remoto y reintentos seguros.

**Estado de implementación:** no aplicado en esta auditoría; resultado dinámico pendiente.

**Enlace:** https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/persistence/supabase_repository_adapter.py#L114

### FU-03 — Carga del PDF a memoria sin límite visible en endpoint
**Componente:** src/adapters/inbound/api/expediente_router.py (líneas 31–50) · **Prioridad preliminar:** Media · **Factor:** P / R

**Evidencia de código:** Se usa await archivo_pdf.read() sin un tamaño máximo explícito en el handler inspeccionado.

**Riesgo:** Posible agotamiento de recursos frente a archivos grandes si no existen límites efectivos aguas arriba.

**Comprobación requerida:** PDF cercano al límite, superior al límite y de tipo no soportado; verificar 413/422 y estabilidad.

**Recomendación:** Establecer tamaño máximo, tipo permitido y gestión de archivos inválidos con respuesta controlada.

**Estado de implementación:** no aplicado en esta auditoría; resultado dinámico pendiente.

**Enlace:** https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/inbound/api/expediente_router.py#L31


## Validaciones de la guía
Inicio de sesión: respuestas válidas/inválidas. Sesión: expiración y firma JWT. API: 401/403 en rutas privadas y 2xx legítimas. Roles: principio de mínimo privilegio. Formularios: tamaño/tipo/errores de entrada. Integraciones: errores HTTP de Supabase.

## Rollback
Crear commits aislados en rama de trabajo, documentar un comando de revert por PR y guardar métricas de comparación. No se han aplicado estos cambios en la versión examinada.

## Alineación con OWASP Top 10:2025

- A01:2025 (acceso): OW-02 y OW-03; exigir autorización efectiva en ambas APIs. SSRF pertenece a esta categoría en la versión 2025, pero SIMEL aún no tiene prueba de explotación SSRF.
- A04:2025 y A07:2025 (criptografía y autenticación): OW-01; corregir y probar validación del hash.
- A03:2025 (cadena de suministro): revisar dependencias con versiones, SBOM y escaneo, sin afirmar CVEs no detectadas.
- A09:2025 (registro y alertas): FU-02; emitir observabilidad segura de fallas.
- A10:2025 (excepciones): FU-01 y FU-02; manejar errores sin fallar de modo abierto ni silenciarlos.

Esta tabla amplía las prioridades ya definidas y **no equivale a remediación aplicada**. Fuente: https://top10.owasp.org/2025/es/.