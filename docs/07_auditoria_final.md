# SIMEL — 07 — Auditoría final integral: dictamen PROVISIONAL

**Curso:** Taller de Proyectos 1 — Semana 13, 12/11/2026.
**Repositorio:** https://github.com/Ronaldogh179/proyecto-licencias
**Código auditado (commit fijo):** `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88`.
**Base:** SIMEL_SEMANA12(4).docx; Guía FURPS+ y OWASP(2).docx; transcripción docente.
**Método:** inspección estática del código por conexión GitHub. No se han ejecutado pruebas dinámicas nuevas ni aplicado remediaciones. El informe de semana 12 (4) fue verificado como ejemplar disponible; no se dispone de la versión (3) para comprobar equivalencia.

## Resumen y límites

Se confirmaron por lectura de código del commit auditado cinco hallazgos principales (OW-01/02/03, FU-01/02), además de FU-03 y la brecha QA-01. Se revisó la matriz oficial OWASP Top 10:2025, conservando la equivalencia con el material del docente. Los planes de mejora existen, **pero no se aplicaron los cambios ni se ejecutaron nuevas pruebas**.

## Dictamen por dimensión

| Dimensión | Estado demostrable |
|---|---|
| Calidad FURPS+ | Parcial por inspección; falta validación operacional actual |
| Seguridad OWASP 2025 | No conforme en controles críticos observados, sin prueba dinámica de cierre |
| Preservación funcional | No se han aplicado cambios; pruebas de regresión posteriores pendientes |
| Riesgo operativo | Alto provisional en autenticación/autorización para expedientes reales |
| Producción | NO APTO en el estado del código inspeccionado; reevaluación obligatoria |

## Cumplimiento del apartado 10 de la guía

- Mejoras críticas implementadas: **NO**.
- Sin hallazgos críticos pendientes: **NO**.
- Vulnerabilidades críticas mitigadas: **NO**.
- Riesgos residuales documentados: **SÍ**.
- Ausencia de regresiones: **NO EVALUADA**.
- Compilación, despliegue y pruebas críticas sobre SHA correctivo: **PENDIENTES**.

## Próximo control

Tras remediaciones, anexar PR/commits correctivos, comandos de pruebas, resultados HTTP 401/403 y 2xx, resultados de PyTest/cobertura/Render, evidencia de Supabase y capturas literales del navegador o IDE del antes/después. Solo entonces emitir dictamen final definitivo.

**Declaración:** esta auditoría es un informe provisional académico, no un pentest ni una certificación OWASP.
