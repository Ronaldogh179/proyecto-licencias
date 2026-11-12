# SIMEL — 05 — Plan de remediación OWASP Top 10:2025

**Curso:** Taller de Proyectos 1 — Semana 13, 12/11/2026.
**Repositorio:** https://github.com/Ronaldogh179/proyecto-licencias
**Código auditado (commit fijo):** `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88`.
**Base:** SIMEL_SEMANA12(4).docx; Guía FURPS+ y OWASP(2).docx; transcripción docente.
**Método:** inspección estática del código por conexión GitHub. No se han ejecutado pruebas dinámicas nuevas ni aplicado remediaciones. El informe de semana 12 (4) fue verificado como ejemplar disponible; no se dispone de la versión (3) para comprobar equivalencia.

## Objetivo y principio de preservación

Corregir debilidades de autenticación, autorización, errores y sincronización sin romper HU01–HU08, esquemas, usuarios ni integraciones. Priorizar controles críticos primero.

| Orden | ID / categoría 2025 | Impacto y prioridad | Remediación | Validación |
|---|---|---|---|---|
| 1 | OW-01 — A07:2025, A04:2025 | Crítica: Un usuario existente podría autenticarse con una clave incorrecta. | Sustituir por verificación real de hash resistente (Argon2/bcrypt), migrar fixture de credenciales y evitar fallback. | Login correcto 200; contraseña incorrecta 401; usuario inexistente 401. |
| 2 | OW-02 — A01:2025 | Crítica: Posibles operaciones sin identidad ni permisos verificados; requiere comprobación HTTP. | Dependencia centralizada de autenticación/autorización con permisos mínimos y rutas protegidas. | Sin JWT 401, token inválido 401, rol insuficiente 403, funcionario válido 2xx. |
| 3 | OW-03 — A01:2025, A06:2025 | Alta: Un usuario podría emitir un JWT con rol mayor al registrado; impacto pendiente de test. | Tomar rol únicamente del registro autorizado del usuario; probar escalamiento. | Solicitar rol no permitido: token refleja rol almacenado o solicitud es rechazada. |
| 4 | FU-01 — A10:2025, A06:2025 | Alta: Errores de documentos pueden pasar inadvertidos y afectar el resultado ML. | Señalar PDF corrupto/escaneado/sin texto y resultado verificable; no atribuir confianza ficticia. | PDF digital, escaneado, corrupto y sin adjunto: salida diferenciada. |
| 5 | FU-02 — A09:2025, A10:2025 | Alta: Podría confundirse persistencia local con remota exitosa. | Comprobar estado de respuesta, registro seguro, estado de sincronización y reintentos controlados. | Mock de 401, 500, timeout, desconexión y reconciliación de registros. |
| 6 | FU-03 — A06:2025, A10:2025 | Media: Posible presión sobre memoria con archivos grandes, si no existe límite de infraestructura. | Límites de tamaño, tipo MIME validado y error 413/422 controlado. | Archivos debajo/encima del límite, corruptos y formato no válido. |

## Aplicación escalonada

1. Baseline de pruebas y entorno de trabajo aislado, respaldar configuración de usuarios. 2. Verificar hashes reales y roles confiables. 3. Añadir dependencia de JWT/permisos a rutas. 4. Normalizar errores PDF y carga de archivos. 5. Comprobar respuestas remotas, registros seguros y alertas. 6. Ejecutar pruebas unitarias, integración, autorización y regresión; revisar diff/PR.

## Reversión y riesgo residual

Un commit por corrección y revisión independiente de QA. Revertir solo en entornos de prueba cuando exista riesgo de restituir la vulnerabilidad; no abrir rutas privadas en producción. No exponer claves, JWT ni datos de expedientes en evidencias. Validar autenticación, sesiones, APIs, roles, formularios e integraciones según apartado 8 de la guía.

## Estado

Plan diseñado, **sin implementación ni pruebas posteriores**. Categorías A02/A03/A05/A08 requieren auditorías específicas adicionales para concluir.
