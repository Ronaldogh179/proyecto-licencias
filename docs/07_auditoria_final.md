# Proyecto SIMEL — Taller de Proyectos 1 / Semana 13

Repositorio: https://github.com/Ronaldogh179/proyecto-licencias
Instantánea auditada: `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` (rama `main`, corte de código revisado y confirmado 12/11/2026).
Base documental: `SIMEL_SEMANA12(4).docx`, `Guia FURPS+ y OWASP(2).docx` y transcripción de clase.
Fecha documental: 12/11/2026.
**Alcance:** inspección estática de código GitHub en commit inmutable y resultados históricos diferenciados. Se actualizaron únicamente documentos de auditoría; no se modificó código ejecutable ni se realizaron pruebas dinámicas nuevas. La publicación de los Markdown en GitHub es documental, no remediación.

**Aclaración documental:** se revisó el ejemplar proporcionado `SIMEL_SEMANA12(4).docx`. No se dispone del archivo `(3)` para acreditar que sea idéntico. Las cifras históricas solo se atribuyen al informe consultado.

# 07 — Dictamen integral (PROVISIONAL, NO FINAL)

## Resumen
La revisión estática detectó debilidades de validación de contraseñas, autorización de rutas, selección de rol, tratamiento de PDF y observabilidad de sincronización. Se observan arquitectura hexagonal y pruebas en el repositorio, pero no se ejecutaron nuevos ensayos.

## Estado de calidad
Cumplimiento **parcial no certificado**: existe implementación y documentación previa; faltan remediaciones y pruebas actuales.

## Estado de seguridad
**No conforme en controles críticos observados**: no recomendar exposición a producción hasta corregir autenticación y autorización. No constituye pentest ni certificado OWASP.

## Funcionalidad y regresiones
Sin cambios aplicados. La preservación funcional posterior no ha sido verificada; no puede afirmarse ausencia de regresiones.

## Riesgo operativo
Alto por autenticación/autorización; carácter provisional.

## Dictamen provisional
**No apto para producción en el estado del código inspeccionado**; pendiente de validación integral tras nuevas pruebas y remediaciones.

## Próximo control
Adjuntar capturas reales GitHub/IDE de cada hallazgo, pruebas de 401/403, suite PyTest actual, test de carga actual, estado de Supabase y commits de corrección. Solo entonces emitir el dictamen final solicitado en la guía.

## Coherencia de hallazgos y estado

|Hallazgo|Categoría principal|Referencia complementaria|Evidencia|Estado 12/11/2026|
|---|---|---|---|---|
|OW-01|OWASP A07:2025 / A04:2025|FURPS+ F|`config.py` 45–47|Confirmado por lectura de código; remediación pendiente|
|OW-02|OWASP A01:2025|FURPS+ F|`expediente_router.py` 31–49 y `pmv2_router.py` 47–66|Ausencia de dependencia en handlers observada; exposición efectiva pendiente de prueba|
|OW-03|OWASP A01:2025 / A06:2025|FURPS+ F|`procesar_expediente_uc.py` 22–39|Propagación del rol observada; abuso de privilegios pendiente de prueba|
|FU-01|FURPS+ R (fiabilidad)|OWASP A10:2025|`tesseract_ocr_adapter.py` 16–26, 53–59|Confirmado por lectura; pruebas de PDF y corrección pendientes|
|FU-02|FURPS+ R/S|OWASP A09:2025 / A10:2025|`supabase_repository_adapter.py` 114–138|Confirmado por lectura; impacto operativo pendiente de prueba|

**Total:** cinco hallazgos prioritarios únicos, sin doble conteo transversal. Se documentan también FU-03 y QA-01 en las auditorías complementarias; no constituyen pruebas de corrección.


## Validación documental del corte de semana 13 (12/11/2026)

- Los hallazgos OW-01, OW-02, OW-03, FU-01 y FU-02 fueron **corroborados por lectura de código** del commit auditado, con visualizaciones de extractos de líneas exactas, SHA y permalinks.
- La matriz OWASP se actualizó a **2025** con equivalencia a la clasificación 2021 de los archivos del docente.
- Los informes y planes son entregables iniciales; **no** se ejecutaron las dos etapas de implementación ni la auditoría integral posterior.
- La publicación de documentos en `docs/` no cambia el estado de los hallazgos de producto.

El dictamen continúa siendo **provisional** hasta que exista código corregido, pruebas de aceptación/regresión y validación independiente.