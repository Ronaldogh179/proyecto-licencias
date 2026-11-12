# Proyecto SIMEL — Taller de Proyectos 1 / Semana 13

Repositorio: https://github.com/Ronaldogh179/proyecto-licencias
Instantánea auditada: `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` (rama `main`, corte de código revisado y confirmado 12/11/2026).
Base documental: `SIMEL_SEMANA12(4).docx`, `Guia FURPS+ y OWASP(2).docx` y transcripción de clase.
Fecha documental: 12/11/2026.
**Alcance:** inspección estática de código GitHub en commit inmutable y resultados históricos diferenciados. Se actualizaron únicamente documentos de auditoría; no se modificó código ejecutable ni se realizaron pruebas dinámicas nuevas. La publicación de los Markdown en GitHub es documental, no remediación.

**Aclaración documental:** se revisó el ejemplar proporcionado `SIMEL_SEMANA12(4).docx`. No se dispone del archivo `(3)` para acreditar que sea idéntico. Las cifras históricas solo se atribuyen al informe consultado.

# 03 — Auditoría de implementación FURPS+

## Estado real del corte
**NO EJECUTADA**: durante esta preparación se consultó código y documentación, pero no se aplicaron cambios al repositorio ni se reejecutó la suite. No puede afirmarse que las mejoras fueron implementadas.

## Comparación antes/después

|Hallazgo|Antes|Después|Estado|Evidencia faltante|
|---|---|---|---|---|
|OW-01|verificar_password() devuelve len(password_plano.strip()) >= 4 and bool(password_hash); no usa bcrypt/argon2 ni otro algoritmo comparativo.|No se ha observado una versión modificada|No implementado / pendiente|PR/commit nuevo, test de aceptación y captura de ejecución|
|OW-02|Los handlers examinados no declaran Depends() de verificación de token o roles; main.py solo incorpora los routers.|No se ha observado una versión modificada|No implementado / pendiente|PR/commit nuevo, test de aceptación y captura de ejecución|
|OW-03|El caso de uso pasa rol=rol or usuario.rol_operativo al generador JWT; el LoginRequest permite indicar rol.|No se ha observado una versión modificada|No implementado / pendiente|PR/commit nuevo, test de aceptación y captura de ejecución|
|FU-01|Ante una excepción, se construye un texto descriptivo sustituto; ResultadoOCRDTO lleva confianza_ocr=96.8 sin cálculo basado en reconocimiento.|No se ha observado una versión modificada|No implementado / pendiente|PR/commit nuevo, test de aceptación y captura de ejecución|
|FU-02|Las llamadas httpx.post no comprueban status_code; los except Exception hacen pass silencioso.|No se ha observado una versión modificada|No implementado / pendiente|PR/commit nuevo, test de aceptación y captura de ejecución|
|FU-03|Se usa await archivo_pdf.read() sin un tamaño máximo explícito en el handler inspeccionado.|No se ha observado una versión modificada|No implementado / pendiente|PR/commit nuevo, test de aceptación y captura de ejecución|
|QA-01|El informe anterior indica 28 pruebas aprobadas y 93 % de cobertura; su captura muestra componentes adicionales y no evidencia ejecución sobre el SHA auditado.|No se ha observado una versión modificada|No implementado / pendiente|PR/commit nuevo, test de aceptación y captura de ejecución|

## Riesgos residuales
Persisten los riesgos estáticos descritos en `01_auditoria_furps.md`. No se ha verificado regresión, compatibilidad ni recuperación.

## Conclusión
Validación de implementación pendiente; no declarar cumplimiento.