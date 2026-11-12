# Proyecto SIMEL — Taller de Proyectos 1 / Semana 13

Repositorio: https://github.com/Ronaldogh179/proyecto-licencias
Instantánea auditada: `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` (rama `main`, corte de código revisado y confirmado 12/11/2026).
Base documental: `SIMEL_SEMANA12(4).docx`, `Guia FURPS+ y OWASP(2).docx` y transcripción de clase.
Fecha documental: 12/11/2026.
**Alcance:** inspección estática de código GitHub en commit inmutable y resultados históricos diferenciados. Se actualizaron únicamente documentos de auditoría; no se modificó código ejecutable ni se realizaron pruebas dinámicas nuevas. La publicación de los Markdown en GitHub es documental, no remediación.

**Aclaración documental:** se revisó el ejemplar proporcionado `SIMEL_SEMANA12(4).docx`. No se dispone del archivo `(3)` para acreditar que sea idéntico. Las cifras históricas solo se atribuyen al informe consultado.

# 04 — Auditoría OWASP Top 10:2025 con trazabilidad a la guía docente

## Matriz oficial OWASP Top 10:2025 y equivalencia con el material del docente

La guía del curso enumera las categorías con los nombres y orden de OWASP Top 10:2021. El docente menciona la edición 2025 en clase. Se incluyen **ambas referencias sin mezclarlas**. La columna «equivalencia» es temática/orientativa, no uno-a-uno: A03:2025 amplía el alcance de componentes vulnerables y A10:2025 es nueva; SSRF se integra en A01:2025.

Fuente oficial OWASP (consulta 12/11/2026): https://top10.owasp.org/2025/es/ y https://top10.owasp.org/2025/0x00_2025-Introduction/

| OWASP 2025 | Riesgo oficial (español) | Relación con categorías de la guía (2021) | SIMEL | Conclusión según código observado |
|---|---|---|---|---|
| A01:2025 | Pérdida de control de acceso | A01:2021; SSRF de A10:2021 | OW-02, OW-03 | Brecha estática; falta prueba HTTP 401/403 y alcance SSRF |
| A02:2025 | Configuración de seguridad incorrecta | A05:2021 | — | No evaluado completamente (CORS, debug, secretos, despliegue) |
| A03:2025 | Fallas en la cadena de suministro de software | A06:2021 (ampliado) | — | Dependencias sin versiones fijadas; sin SCA/SBOM/CVE confirmado |
| A04:2025 | Fallas criptográficas | A02:2021 | OW-01 | Problema en verificación de contraseña; auditar gestión JWT |
| A05:2025 | Inyección | A03:2021 | — | Sin prueba específica de entradas / consultas |
| A06:2025 | Diseño inseguro | A04:2021 | OW-03, FU-01 | Riesgo de roles y manejo documental; evidencia estática |
| A07:2025 | Fallas de autenticación | A07:2021 | OW-01 | Verificador no compara hash almacenado |
| A08:2025 | Fallas en integridad del software o los datos | A08:2021 | — | Falta auditoría CI, artefactos y procedencia |
| A09:2025 | Fallas de registro, alertas y monitoreo de seguridad | A09:2021 | FU-02 | Errores de sincronización ocultados; falta observar alertas |
| A10:2025 | Manejo inadecuado de condiciones excepcionales | Nueva categoría 2025 | FU-01, FU-02 | Fallback de PDF y except pass; evaluación de impactos pendiente |

**Criterio de interpretación:** «sin prueba» significa *no evaluado*, no «seguro»; hallazgo estático no equivale a explotación confirmada. No se ha emitido una nota/score global OWASP porque faltan pruebas sistemáticas y validación de todas las categorías.

## Tabla conservada de equivalencia: clasificación utilizada en la guía del ingeniero (OWASP 2021)

## Matriz de cobertura por categoría según la guía docente (orden de OWASP 2021)

|Categoría|Referencia guía|Hallazgo inspeccionado|Estado|Vinculación|
|---|---|---|---|---|
|A01|Broken Access Control|Control de acceso roto: endpoints privados sin Depends/JWT visible|Inspección positiva de brecha|OW-02|
|A02|Cryptographic Failures|Contraseña no se compara con hash; HS256 configurado para emisión|Brecha de contraseña; JWT parcial|OW-01|
|A03|Injection|Sin prueba de inyección o auditoría completa SQL/entrada|Sin evidencia para dictamen|Pendiente|
|A04|Insecure Design|Rol definido por el cliente en token; manejo débil de errores|Brecha de diseño|OW-03, FU-01|
|A05|Security Misconfiguration|Revisar documentación pública, variables de entorno, CORS, debug|No evaluado por completo|Pendiente|
|A06|Vulnerable Components|requirements sin fijación visible; sin SCA/SBOM|Riesgo sin CVE confirmada|Pendiente|
|A07|Identification and Authentication Failures|Autenticación confía en longitud de contraseña|Inspección positiva de brecha|OW-01|
|A08|Software and Data Integrity Failures|No hay comprobación de firmas/CI y permisos de artefactos|Pendiente de evaluación|Pendiente|
|A09|Security Logging and Monitoring Failures|Except pass en sincronización, visibilidad insuficiente|Brecha de observabilidad|FU-02|
|A10|Server-Side Request Forgery (SSRF)|No se ha corroborado SSRF: destino Supabase controlado por entorno|Sin evidencia para dictamen|Pendiente|

## Hallazgos priorizados
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


## Impacto/probabilidad/score global
Las prioridades son **preliminares y cualitativas**. No se asigna score global cuantitativo sin pruebas reproducibles, cobertura completa y matriz de riesgo aprobada. No se ha practicado explotación ni escaneo dinámico.

## Evidencias
Código del commit en los enlaces de cada ficha; las imágenes E01–E05 dentro del Word son **extractos gráficos de código consultado**, no capturas de pantalla del navegador.

## Procedencia visual de evidencia confirmada

Las fichas EV01–EV05 del ZIP incluyen enlaces permanentes y capturas reales de la interfaz GitHub del SHA auditado. Las imágenes muestran evidencia de inspección estática; no se realizaron pruebas dinámicas ni se verificó explotación.