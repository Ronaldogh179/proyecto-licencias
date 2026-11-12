# SIMEL — 02 — Plan de mejoras FURPS+

**Curso:** Taller de Proyectos 1 — Semana 13, 12/11/2026.
**Repositorio:** https://github.com/Ronaldogh179/proyecto-licencias
**Código auditado (commit fijo):** `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88`.
**Base:** SIMEL_SEMANA12(4).docx; Guía FURPS+ y OWASP(2).docx; transcripción docente.
**Método:** inspección estática del código por conexión GitHub. No se han ejecutado pruebas dinámicas nuevas ni aplicado remediaciones. El informe de semana 12 (4) fue verificado como ejemplar disponible; no se dispone de la versión (3) para comprobar equivalencia.

## Propósito

Preservar el flujo HU01–HU08 en los PMV1 y PMV2, corregir los hallazgos progresivamente y preservar compatibilidad API, usuarios y bases de datos.

## Plan de ejecución priorizado

| Orden | Hallazgo | Prioridad | Responsable | Corrección y comprobación |
|---|---|---|---|---|
| 1 | OW-01 | Crítica | Backend + QA | Sustituir por verificación real de hash resistente (Argon2/bcrypt), migrar fixture de credenciales y evitar fallback. Prueba: Login correcto 200; contraseña incorrecta 401; usuario inexistente 401. |
| 2 | OW-02 | Crítica | Integración + QA | Dependencia centralizada de autenticación/autorización con permisos mínimos y rutas protegidas. Prueba: Sin JWT 401, token inválido 401, rol insuficiente 403, funcionario válido 2xx. |
| 3 | OW-03 | Alta | Backend + QA | Tomar rol únicamente del registro autorizado del usuario; probar escalamiento. Prueba: Solicitar rol no permitido: token refleja rol almacenado o solicitud es rechazada. |
| 4 | FU-01 | Alta | Backend/ML + QA | Señalar PDF corrupto/escaneado/sin texto y resultado verificable; no atribuir confianza ficticia. Prueba: PDF digital, escaneado, corrupto y sin adjunto: salida diferenciada. |
| 5 | FU-02 | Alta | Integración + QA | Comprobar estado de respuesta, registro seguro, estado de sincronización y reintentos controlados. Prueba: Mock de 401, 500, timeout, desconexión y reconciliación de registros. |
| 6 | FU-03 | Media | Integración + QA | Límites de tamaño, tipo MIME validado y error 413/422 controlado. Prueba: Archivos debajo/encima del límite, corruptos y formato no válido. |
| 7 | QA-01 | Media | QA | Fijar dependencias, ejecutar pytest, pytest-cov, guardar comandos, entorno y salida. Prueba: pytest -q; pytest --cov=src --cov-report=term-missing, resultados sin alterar. |

## Cronograma sugerido

Semana 13: inspección, validación del código por SHA, matriz de riesgos y plan. Semana 14: corregir OW-01/OW-02/OW-03; luego FU-01/FU-02/FU-03 en rama de trabajo, con pruebas aisladas y revisiones. Semana 15: ejecutar regresiones, métricas y emitir auditorías de implementación y cierre. Son hitos propuestos, no actividades ya ejecutadas.

## Estrategia transversal

Antes de cambios: fijar baseline, guardar pruebas originales y contratos. Durante implementación: un commit verificable por hallazgo, cambios mínimos y pruebas positivas/negativas. Después: PR revisado, evidencia, comprobación de despliegue, evaluación de impacto y rollback por commit. No restablecer vulnerabilidades críticas en producción como método de rollback. Documentar fallos en lugar de ocultarlos.

**Estado:** plan definido, cambios **no aplicados** a la versión auditada.
