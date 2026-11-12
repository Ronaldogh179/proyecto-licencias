# Proyecto SIMEL — Taller de Proyectos 1 / Semana 13

Repositorio: https://github.com/Ronaldogh179/proyecto-licencias
Instantánea auditada: `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` (rama `main`, corte de código revisado y confirmado 12/11/2026).
Base documental: `SIMEL_SEMANA12(4).docx`, `Guia FURPS+ y OWASP(2).docx` y transcripción de clase.
Fecha documental: 12/11/2026.
**Alcance:** inspección estática de código GitHub en commit inmutable y resultados históricos diferenciados. Se actualizaron únicamente documentos de auditoría; no se modificó código ejecutable ni se realizaron pruebas dinámicas nuevas. La publicación de los Markdown en GitHub es documental, no remediación.

**Aclaración documental:** se revisó el ejemplar proporcionado `SIMEL_SEMANA12(4).docx`. No se dispone del archivo `(3)` para acreditar que sea idéntico. Las cifras históricas solo se atribuyen al informe consultado.

# 01 — Auditoría FURPS+ (línea base)

## Resumen ejecutivo
Existen módulos PMV 1 y 2 y una estructura de puertos/adaptadores. La inspección identifica problemas de autenticación, autorización, errores PDF y persistencia; no valida cumplimiento funcional en ejecución ni un score final.

## Matriz provisional del modelo del docente
Escala referencial de Semana13.pdf: 5=cumple en la evidencia revisada; 3=parcial; 1=no cumple; NE=no evaluado. **Los puntajes son de inspección y NO equivalen a certificación de calidad ni prueba operacional.**

|Factor|ID|Criterio|Evidencia|PO|PD|Acción|
|---|---|---|---|---:|---:|---|
|F|F01|Existe flujo de autenticación en API|Código de ruta /auth/login; verificación defectuosa|3|5|Parcial: implementar verificación de contraseña; prueba HTTP.|
|F|F02|Existe procesamiento y bandeja de expedientes|expediente_router.py: evaluar y bandeja|5|5|Presencia de implementación; verificar ejecución real.|
|F|F03|Existen operaciones PMV 2: indexación y auditoría|pmv2_router.py: rutas POST y GET|5|5|Presencia de implementación; probar endpoints y resultados.|
|F|F04|Las operaciones privadas exigen JWT/rol|Routers sin dependencia de seguridad visible|1|5|Agregar control de acceso y test 401/403.|
|U|U01|Hay interfaz para ingresar y revisar datos|Informe SIMEL Semana 12 (capturas históricas del informe base; no reejecutadas)|3|5|Revisión de usabilidad y errores en ambiente actual pendiente.|
|U|U02|Se verificó accesibilidad WCAG y navegación|No hay evaluación accesibilidad actual|NE|5|Ejecutar controles de teclado/contraste y pruebas con usuarios.|
|R|R01|Los PDF inválidos generan error verificable|Fallback textual sintético ante excepciones|1|5|Definir rechazo o estado explícito.|
|R|R02|La sincronización remota registra respuesta|httpx.post + except pass|1|5|Persistencia verificable y reporte de error.|
|R|R03|Existe mecanismo de persistencia local alterna|Repositorio híbrido JSON local|5|5|Existencia de código; probar cortes de conexión.|
|P|P01|Existen mediciones de carga de 600 y 1000|Informe SIMEL Semana 12 (mediciones históricas; capturas no reproducidas)|3|5|Repetir mediciones para la versión auditada.|
|P|P02|Las cargas PDF tienen límite comprobable|await archivo_pdf.read() sin límite en handler|1|5|Agregar validación de tamaño y tipo.|
|S|S01|El código está distribuido en capas hexagonales|domain/application/adapters/infrastructure|5|5|Verificar reglas de dependencia en auditoría futura.|
|S|S02|Existen pruebas unitarias y de integración|Carpetas tests/unit y tests/integration|5|5|Ejecutar pruebas, cubrir casos negativos de seguridad.|
|S|S03|Dependencias reproducibles y fijadas|requirements.txt sin versiones explícitas (según lista revisada)|1|5|Bloquear versiones y revisar CVE en dependencias.|

Nivel de apego por factor solo para criterios puntuados: F 70,0 % (14/20); U 60,0 % (3/5, otro NE); R 46,7 % (7/15); P 40,0 % (4/10); S 73,3 % (11/15). Estos son índices parciales de inspección y no un score global.

## Hallazgos
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

### FU-01 — La extracción PDF encubre errores y asigna confianza fija
**Componente:** src/adapters/outbound/ocr/tesseract_ocr_adapter.py (líneas 16–24 y 48–59) · **Prioridad preliminar:** Alta · **Factor:** F / R

**Evidencia de código:** Ante una excepción, se construye un texto descriptivo sustituto; ResultadoOCRDTO lleva confianza_ocr=96.8 sin cálculo basado en reconocimiento.

**Riesgo:** Clasificación a partir de contenido no extraído y percepción engañosa de confianza del procesamiento.

**Comprobación requerida:** Pruebas con PDF digital válido, escaneado, vacío/corrupto y sin archivo; verificar estado y trazabilidad.

**Recomendación:** Diferenciar PDF digital, PDF escaneado, PDF inválido y ausencia de adjunto; definir error o estado revisable, sin confianza inventada.

**Estado de implementación:** no aplicado en esta auditoría; resultado dinámico pendiente.

**Enlace:** https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/ocr/tesseract_ocr_adapter.py#L16

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

### QA-01 — Pruebas históricas sin reproducción atribuible a commit actual
**Componente:** SIMEL_SEMANA12(4).docx, Anexo 4; tests/ del repositorio (líneas Anexo 4 / árbol de pruebas) · **Prioridad preliminar:** Media · **Factor:** S / P

**Evidencia de código:** El informe anterior indica 28 pruebas aprobadas y 93 % de cobertura; su captura muestra componentes adicionales y no evidencia ejecución sobre el SHA auditado.

**Riesgo:** No puede inferirse el rendimiento ni la cobertura actual de cada PMV solo desde una captura anterior.

**Comprobación requerida:** pytest -q; pytest --cov=src --cov-report=term-missing; comparar con baseline sin asumir equivalencia.

**Recomendación:** Crear baseline reproducible del commit, ejecutar pytest/cobertura y registrar por separado PMV 1 y PMV 2.

**Estado de implementación:** no aplicado en esta auditoría; resultado dinámico pendiente.

**Enlace:** SIMEL_SEMANA12(4).docx, Anexo 4; tests/ del repositorio


## Riesgos residuales
No hay evidencias de pruebas negativas de autorización, análisis automatizado de dependencia, evaluación WCAG ni métricas de memoria actuales.

## Recomendación general
Priorizar autenticación y autorización, luego fallos del procesamiento PDF y sincronización; ejecutar suite de regresión antes/después.

## Verificación adicional de evidencias del corte actual

Se consultaron directamente las líneas del commit `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88` en GitHub para OW-01, OW-02, OW-03, FU-01 y FU-02. Las fichas textuales EV01–EV05 y el manifiesto del ZIP indican los enlaces permanentes a los fragmentos; los paneles gráficos previos se excluyeron por no ser capturas auténticas. **Evidencia estática de código no sustituye prueba dinámica, y los paneles no son capturas de navegador.**