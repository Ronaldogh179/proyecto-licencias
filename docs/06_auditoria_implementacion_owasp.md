# Proyecto SIMEL — Taller de Proyectos 1 / Semana 13

Repositorio: https://github.com/Ronaldogh179/proyecto-licencias
Instantánea auditada: `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` (rama `main`, corte de código revisado y confirmado 12/11/2026).
Base documental: `SIMEL_SEMANA12(4).docx`, `Guia FURPS+ y OWASP(2).docx` y transcripción de clase.
Fecha documental: 12/11/2026.
**Alcance:** inspección estática de código GitHub en commit inmutable y resultados históricos diferenciados. Se actualizaron únicamente documentos de auditoría; no se modificó código ejecutable ni se realizaron pruebas dinámicas nuevas. La publicación de los Markdown en GitHub es documental, no remediación.

**Aclaración documental:** se revisó el ejemplar proporcionado `SIMEL_SEMANA12(4).docx`. No se dispone del archivo `(3)` para acreditar que sea idéntico. Las cifras históricas solo se atribuyen al informe consultado.

# 06 — Auditoría de implementación OWASP

**Estado:** no ejecutada. No hay commits de remediación verificados ni pruebas posteriores.

|Hallazgo|Resultado de remediación|Resultado de prueba|Riesgo residual|
|---|---|---|---|
|OW-01|No implementado / no comprobado|Pendiente: Cuenta autorizada con contraseña correcta = 200; contraseña incorrecta de >=4 caracteres = 401; usuario inexistente = 401.|Un usuario existente podría recibir un token con cualquier contraseña de cuatro o más caracteres, pendiente de prueba controlada.|
|OW-02|No implementado / no comprobado|Pendiente: Sin token 401; token inválido o vencido 401; rol insuficiente 403; usuario legítimo conserva respuestas 2xx.|Acceso potencial a registros, indexación o auditoría sin una identidad validada, sujeto a verificación HTTP.|
|OW-03|No implementado / no comprobado|Pendiente: Solicitar rol de mayor privilegio y verificar que el token refleje solo el rol real o se rechace.|Un usuario con cuenta podría solicitar un rol distinto al registrado; el impacto requiere validación al incorporar autorización.|
|FU-01|No implementado / no comprobado; *hallazgo primario FURPS+ de fiabilidad*, trazado además a A10:2025 (sin duplicarlo).|Pendiente: PDF digital válido, corrupto, escaneado, sin texto, excepción de extracción y sin archivo; verificar ausencia de texto sustituto/indicador de confianza inventado.|El extractor puede aparentar procesamiento satisfactorio sin obtener el texto real.|
|FU-02|No implementado / no comprobado|Pendiente: Simular 401, 500, timeout y corte de red; verificar alertas, respuesta de la API y consistencia.|La copia local puede aparentar sincronización exitosa sin evidencia de persistencia remota.|
|FU-03|No implementado / no comprobado|Pendiente: PDF cercano al límite, superior al límite y de tipo no soportado; verificar 413/422 y estabilidad.|Posible agotamiento de recursos frente a archivos grandes si no existen límites efectivos aguas arriba.|

**Score de seguridad actualizado:** no determinable con la información disponible; no corresponde inventar una mejora numérica.

**Identificador transversal:** FU-01 pertenece a fiabilidad (R) y se relaciona con excepciones (A10:2025). Su seguimiento queda abierto en `02_plan_furps.md`, `03_auditoria_implementacion_furps.md`, `05_plan_owasp.md` y este documento. No se duplica el conteo de hallazgos.


**Conclusión:** pendiente de remediación y reauditoría.

## Alcance de actualización 2025

Se añadió la trazabilidad OWASP Top 10:2025 a los documentos iniciales. Esto es una actualización metodológica documental, **no** una corrección del código ni una reducción demostrada del riesgo. Los riesgos A01, A04, A07, A09 y A10 se mantienen abiertos en la medida indicada por los hallazgos OW-01 a OW-03, FU-01 y FU-02.