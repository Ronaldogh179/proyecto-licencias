# SIMEL — 06 — Auditoría de implementación OWASP

**Curso:** Taller de Proyectos 1 — Semana 13, 12/11/2026.
**Repositorio:** https://github.com/Ronaldogh179/proyecto-licencias
**Código auditado (commit fijo):** `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88`.
**Base:** SIMEL_SEMANA12(4).docx; Guía FURPS+ y OWASP(2).docx; transcripción docente.
**Método:** inspección estática del código por conexión GitHub. No se han ejecutado pruebas dinámicas nuevas ni aplicado remediaciones. El informe de semana 12 (4) fue verificado como ejemplar disponible; no se dispone de la versión (3) para comprobar equivalencia.

## Declaración de estado

**NO EJECUTADA / PENDIENTE.** No se aplicaron correcciones al código para esta entrega documental, ni se reanalizaron controles en ejecución. No se debe atribuir mitigación a la actualización de Markdown a OWASP 2025.

| ID | Estado de remediación | Prueba posterior | Riesgo residual |
|---|---|---|---|
| OW-01 | No implementado / no comprobado | Pendiente: Login correcto 200; contraseña incorrecta 401; usuario inexistente 401. | Un usuario existente podría autenticarse con una clave incorrecta. |
| OW-02 | No implementado / no comprobado | Pendiente: Sin JWT 401, token inválido 401, rol insuficiente 403, funcionario válido 2xx. | Posibles operaciones sin identidad ni permisos verificados; requiere comprobación HTTP. |
| OW-03 | No implementado / no comprobado | Pendiente: Solicitar rol no permitido: token refleja rol almacenado o solicitud es rechazada. | Un usuario podría emitir un JWT con rol mayor al registrado; impacto pendiente de test. |
| FU-01 | No implementado / no comprobado | Pendiente: PDF digital, escaneado, corrupto y sin adjunto: salida diferenciada. | Errores de documentos pueden pasar inadvertidos y afectar el resultado ML. |
| FU-02 | No implementado / no comprobado | Pendiente: Mock de 401, 500, timeout, desconexión y reconciliación de registros. | Podría confundirse persistencia local con remota exitosa. |
| FU-03 | No implementado / no comprobado | Pendiente: Archivos debajo/encima del límite, corruptos y formato no válido. | Posible presión sobre memoria con archivos grandes, si no existe límite de infraestructura. |

## Verificación mínima de cierre según la guía

- Inicio de sesión: credenciales correctas/incorrectas, rechazo comprobado.
- Gestión de sesiones: firma y vencimiento JWT.
- APIs: rechazo de peticiones sin token y con token no autorizado.
- Roles: ninguna identidad puede elegir rol superior.
- Formularios: tipo/tamaño de PDF y respuestas controladas.
- Integraciones: fallas HTTP de Supabase con trazabilidad.

**Score de seguridad actualizado:** N/D. **Conclusión:** hallazgos de seguridad abiertos hasta que existan código corregido, pruebas y evidencia.
