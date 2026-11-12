# Proyecto SIMEL — Taller de Proyectos 1 / Semana 13

Repositorio: https://github.com/Ronaldogh179/proyecto-licencias
Instantánea auditada: `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` (rama `main`, corte de código revisado y confirmado 12/11/2026).
Base documental: `SIMEL_SEMANA12(4).docx`, `Guia FURPS+ y OWASP(2).docx` y transcripción de clase.
Fecha documental: 12/11/2026.
**Alcance:** inspección estática de código GitHub en commit inmutable y resultados históricos diferenciados. Se actualizaron únicamente documentos de auditoría; no se modificó código ejecutable ni se realizaron pruebas dinámicas nuevas. La publicación de los Markdown en GitHub es documental, no remediación.

**Aclaración documental:** se revisó el ejemplar proporcionado `SIMEL_SEMANA12(4).docx`. No se dispone del archivo `(3)` para acreditar que sea idéntico. Las cifras históricas solo se atribuyen al informe consultado.

# 02 — Plan de mejoras FURPS+

**Objetivo:** conservar HU01–HU08 y contratos API, corrigiendo los hallazgos por incrementos.

## Secuencia y responsables sugeridos

|Orden|ID|Prioridad|Responsable sugerido|Implementación|Verificación / rollback|
|---|---|---|---|---|---|
|1|OW-01|Crítica para autenticación|Backend/ML + QA|Implementar un verificador de hashes real; migrar credenciales de demostración a hashes válidos.|Cuenta autorizada con contraseña correcta = 200; contraseña incorrecta de >=4 caracteres = 401; usuario inexistente = 401. Reversión: Revertir el commit y restaurar configuración de usuarios de prueba respaldada, sin dejar credenciales inseguras.|
|2|OW-02|Crítica para control de acceso|Desarrollo/Integración + QA|Agregar dependencia reutilizable que valide firma, expiración y permisos; aplicar en rutas privadas de ambos PMV.|Sin token 401; token inválido o vencido 401; rol insuficiente 403; usuario legítimo conserva respuestas 2xx. Reversión: Revertir cambios por ruta y mantener un ambiente de pruebas aislado; no publicar de nuevo endpoints privados sin protección.|
|3|OW-03|Alta|Backend/ML + QA|Derivar claims de rol únicamente del repositorio de usuarios y comprobar la autorización efectiva.|Solicitar rol de mayor privilegio y verificar que el token refleje solo el rol real o se rechace. Reversión: Revertir política en ambiente controlado; mantener la versión sin escalamiento y añadir validaciones de contrato.|
|4|FU-01|Alta|Backend/ML|Diferenciar PDF digital, PDF escaneado, PDF inválido y ausencia de adjunto; definir error o estado revisable, sin confianza inventada.|Pruebas pendientes con PDF digital válido, PDF inválido o corrupto, PDF escaneado, PDF sin texto extraíble y error forzado durante la extracción; verificar estado, trazabilidad y ausencia de contenido de respaldo presentado como real. Reversión: Restaurar extractor anterior solo para desarrollo controlado y no convertir errores en evaluaciones aprobadas.|
|5|FU-02|Alta para trazabilidad|Desarrollo/Integración|Validar respuesta HTTP; registrar fallos sin exponer datos personales o secretos; señalar estado local/remoto y reintentos seguros.|Simular 401, 500, timeout y corte de red; verificar alertas, respuesta de la API y consistencia. Reversión: Restituir mecanismo local previo y conservar registros de reconciliación, sin borrar transacciones.|
|6|FU-03|Media|Desarrollo/Integración + QA|Establecer tamaño máximo, tipo permitido y gestión de archivos inválidos con respuesta controlada.|PDF cercano al límite, superior al límite y de tipo no soportado; verificar 413/422 y estabilidad. Reversión: Revertir validación de carga si bloquea documentos válidos y ajustar el umbral de manera medida.|
|7|QA-01|Media|QA y pruebas|Crear baseline reproducible del commit, ejecutar pytest/cobertura y registrar por separado PMV 1 y PMV 2.|pytest -q; pytest --cov=src --cov-report=term-missing; comparar con baseline sin asumir equivalencia. Reversión: Registrar diferencias sin editar resultados históricos, restaurar entorno virtual de dependencias.|

## Roadmap
Semana 13: documentar y corroborar hallazgos de inspección. Semana 14: implementar controles críticos en rama de trabajo, con pruebas y pull request. Semana 15: ejecutar regresiones, capturas antes/después y validación integral. Fechas de hitos propuestas, no cronograma aprobado por el equipo.

## Dependencias
Control de contraseñas y roles precede a la protección de rutas. Pruebas de ruta protegida requieren fixtures de usuarios. Reconstrucción del extractor PDF requiere archivos digitales, escaneados y corruptos.

## Criterio de aceptación
Cada cambio incluirá commit, prueba positiva/negativa, resultado de ejecución, evidencia de pantalla y plan de reversión. No modificar ni eliminar datos de producción en pruebas.