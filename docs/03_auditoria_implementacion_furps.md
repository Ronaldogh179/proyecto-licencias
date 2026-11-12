# SIMEL — 03 — Auditoría de implementación FURPS+

**Curso:** Taller de Proyectos 1 — Semana 13, 12/11/2026.
**Repositorio:** https://github.com/Ronaldogh179/proyecto-licencias
**Código auditado (commit fijo):** `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88`.
**Base:** SIMEL_SEMANA12(4).docx; Guía FURPS+ y OWASP(2).docx; transcripción docente.
**Método:** inspección estática del código por conexión GitHub. No se han ejecutado pruebas dinámicas nuevas ni aplicado remediaciones. El informe de semana 12 (4) fue verificado como ejemplar disponible; no se dispone de la versión (3) para comprobar equivalencia.

## Estado del corte de semana 13

**NO EJECUTADA.** No se identificó un commit correctivo posterior al SHA auditado ni se corrió la suite en esta revisión. La publicación documental de esta carpeta no es implementación ni verificación de regresión.

## Comparación antes/después

| ID | Antes verificado por inspección | Después | Validación |
|---|---|---|---|
| OW-01 | verificar_password() comprueba solo que password tenga >=4 caracteres y exista password_hash; no compara ambos. | Sin modificación de código demostrada | Pendiente: Login correcto 200; contraseña incorrecta 401; usuario inexistente 401. |
| OW-02 | Los handlers de indexación y auditoría inspeccionados no declaran dependencia de autorización, situación análoga en el router PMV1. | Sin modificación de código demostrada | Pendiente: Sin JWT 401, token inválido 401, rol insuficiente 403, funcionario válido 2xx. |
| OW-03 | Se usa rol=rol or usuario.rol_operativo al generar el token, y LoginRequest acepta rol enviado por el cliente. | Sin modificación de código demostrada | Pendiente: Solicitar rol no permitido: token refleja rol almacenado o solicitud es rechazada. |
| FU-01 | Except genérico asigna texto descriptivo como si fuera extraído; confianza_ocr es constante 96.8. | Sin modificación de código demostrada | Pendiente: PDF digital, escaneado, corrupto y sin adjunto: salida diferenciada. |
| FU-02 | Las solicitudes httpx.post no validan status_code y las excepciones se silencian con pass. | Sin modificación de código demostrada | Pendiente: Mock de 401, 500, timeout, desconexión y reconciliación de registros. |
| FU-03 | El handler ejecuta await archivo_pdf.read() sin tamaño máximo explícito. | Sin modificación de código demostrada | Pendiente: Archivos debajo/encima del límite, corruptos y formato no válido. |
| QA-01 | Informe de semana 12 describe 28 pruebas y 93 % de cobertura, pero son antecedentes no repetidos sobre el commit actual. | Sin modificación de código demostrada | Pendiente: pytest -q; pytest --cov=src --cov-report=term-missing, resultados sin alterar. |

## Riesgo residual

Persisten los riesgos de autenticación y autorización (críticos), PDF y persistencia (altos), límites de carga y trazabilidad de pruebas (medios). La ausencia de cambio no demuestra compatibilidad operacional ni ausencia de regresión.

## Condición para cierre

Solicitar SHA correctivo, diff/PR, resultado de pruebas pytest y cobertura, logs/capturas reales y pruebas negativas/positivas por ID. Hasta entonces: **pendiente**, sin puntaje final afirmado.
