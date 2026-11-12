# SIMEL — 01 — Auditoría FURPS+ (línea base)

**Curso:** Taller de Proyectos 1 — Semana 13, 12/11/2026.
**Repositorio:** https://github.com/Ronaldogh179/proyecto-licencias
**Código auditado (commit fijo):** `b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88`.
**Base:** SIMEL_SEMANA12(4).docx; Guía FURPS+ y OWASP(2).docx; transcripción docente.
**Método:** inspección estática del código por conexión GitHub. No se han ejecutado pruebas dinámicas nuevas ni aplicado remediaciones. El informe de semana 12 (4) fue verificado como ejemplar disponible; no se dispone de la versión (3) para comprobar equivalencia.

## Resumen ejecutivo

Arquitectura hexagonal y funcionalidades PMV1/PMV2 observables en código. El diagnóstico identifica brechas críticas de autenticación, autorización y manejo de PDF y sincronización. Los puntajes siguientes son **parciales de inspección**, no certificación ni ensayos funcionales.

## Matriz de evaluación FURPS+

Escala docente orientativa: 5=presencia/criterio cumplido en evidencia inspeccionada; 3=parcial; 1=no cumplido; NE=no evaluado. PO=puntaje observado; PD=deseado.

| Factor | ID | Criterio | PO | PD |
|---|---|---|---|---|
| F | F01 | Login JWT implementado pero validación de contraseña deficiente | 3 | 5 |
| F | F02 | Recepción, clasificación y bandeja PMV1 definidas en rutas | 5 | 5 |
| F | F03 | Indexación y auditoría PMV2 definidas en rutas | 5 | 5 |
| F | F04 | Controles JWT/rol en rutas privadas | 1 | 5 |
| U | U01 | Interfaz funcional ilustrada por informe histórico; sin prueba actual | 3 | 5 |
| U | U02 | Accesibilidad WCAG/teclado no verificada | NE | 5 |
| R | R01 | Manejo explícito de error PDF | 1 | 5 |
| R | R02 | Verificación de sincronización remota | 1 | 5 |
| R | R03 | Persistencia local alternativa implementada | 5 | 5 |
| P | P01 | Mediciones históricas 600/1000, sin repetir | 3 | 5 |
| P | P02 | Límite de carga PDF en handler | 1 | 5 |
| S | S01 | Separación domain/application/adapters/infrastructure | 5 | 5 |
| S | S02 | Carpetas de pruebas y tests presentes (ejecución pendiente) | 5 | 5 |
| S | S03 | requirements.txt sin fijación de versiones | 1 | 5 |

Factores puntuados: F 70,0 % (14/20); U 60,0 % (3/5, con otro criterio NE); R 46,7 % (7/15); P 40,0 % (4/10); S 73,3 % (11/15). Los resultados no son un score FURPS+ certificado.

## Hallazgos con evidencia y tratamiento

### OW-01 — Verificación de contraseña sin cotejo de hash

- **Severidad preliminar:** Crítica; **referencia:** A07:2025, A04:2025.
- **Evidencia:** [src/infrastructure/config.py:L45-L47](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/infrastructure/config.py#L45). verificar_password() comprueba solo que password tenga >=4 caracteres y exista password_hash; no compara ambos.
- **Riesgo:** Un usuario existente podría autenticarse con una clave incorrecta.
- **Plan:** Sustituir por verificación real de hash resistente (Argon2/bcrypt), migrar fixture de credenciales y evitar fallback.
- **Prueba de aceptación pendiente:** Login correcto 200; contraseña incorrecta 401; usuario inexistente 401.
- **Responsable propuesto:** Backend + QA. **Estado de implementación:** pendiente; no se presume corregido.

### OW-02 — Rutas PMV1 y PMV2 sin dependencia explícita de JWT

- **Severidad preliminar:** Crítica; **referencia:** A01:2025.
- **Evidencia:** [src/adapters/inbound/api/pmv2_router.py:L47-L66](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/inbound/api/pmv2_router.py#L47). Los handlers de indexación y auditoría inspeccionados no declaran dependencia de autorización, situación análoga en el router PMV1.
- **Riesgo:** Posibles operaciones sin identidad ni permisos verificados; requiere comprobación HTTP.
- **Plan:** Dependencia centralizada de autenticación/autorización con permisos mínimos y rutas protegidas.
- **Prueba de aceptación pendiente:** Sin JWT 401, token inválido 401, rol insuficiente 403, funcionario válido 2xx.
- **Responsable propuesto:** Integración + QA. **Estado de implementación:** pendiente; no se presume corregido.

### OW-03 — Rol controlado por el cliente llega al JWT

- **Severidad preliminar:** Alta; **referencia:** A01:2025, A06:2025.
- **Evidencia:** [src/application/use_cases/procesar_expediente_uc.py:L22-L39](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/application/use_cases/procesar_expediente_uc.py#L22). Se usa rol=rol or usuario.rol_operativo al generar el token, y LoginRequest acepta rol enviado por el cliente.
- **Riesgo:** Un usuario podría emitir un JWT con rol mayor al registrado; impacto pendiente de test.
- **Plan:** Tomar rol únicamente del registro autorizado del usuario; probar escalamiento.
- **Prueba de aceptación pendiente:** Solicitar rol no permitido: token refleja rol almacenado o solicitud es rechazada.
- **Responsable propuesto:** Backend + QA. **Estado de implementación:** pendiente; no se presume corregido.

### FU-01 — Fallback engañoso ante errores de extracción PDF

- **Severidad preliminar:** Alta; **referencia:** A10:2025, A06:2025.
- **Evidencia:** [src/adapters/outbound/ocr/tesseract_ocr_adapter.py:L16-L26; L58](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/ocr/tesseract_ocr_adapter.py#L16). Except genérico asigna texto descriptivo como si fuera extraído; confianza_ocr es constante 96.8.
- **Riesgo:** Errores de documentos pueden pasar inadvertidos y afectar el resultado ML.
- **Plan:** Señalar PDF corrupto/escaneado/sin texto y resultado verificable; no atribuir confianza ficticia.
- **Prueba de aceptación pendiente:** PDF digital, escaneado, corrupto y sin adjunto: salida diferenciada.
- **Responsable propuesto:** Backend/ML + QA. **Estado de implementación:** pendiente; no se presume corregido.

### FU-02 — Sincronización remota oculta fallos

- **Severidad preliminar:** Alta; **referencia:** A09:2025, A10:2025.
- **Evidencia:** [src/adapters/outbound/persistence/supabase_repository_adapter.py:L114-L138](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/outbound/persistence/supabase_repository_adapter.py#L114). Las solicitudes httpx.post no validan status_code y las excepciones se silencian con pass.
- **Riesgo:** Podría confundirse persistencia local con remota exitosa.
- **Plan:** Comprobar estado de respuesta, registro seguro, estado de sincronización y reintentos controlados.
- **Prueba de aceptación pendiente:** Mock de 401, 500, timeout, desconexión y reconciliación de registros.
- **Responsable propuesto:** Integración + QA. **Estado de implementación:** pendiente; no se presume corregido.

### FU-03 — Lectura completa de PDF sin límite declarado

- **Severidad preliminar:** Media; **referencia:** A06:2025, A10:2025.
- **Evidencia:** [src/adapters/inbound/api/expediente_router.py:L31-L50](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/src/adapters/inbound/api/expediente_router.py#L31). El handler ejecuta await archivo_pdf.read() sin tamaño máximo explícito.
- **Riesgo:** Posible presión sobre memoria con archivos grandes, si no existe límite de infraestructura.
- **Plan:** Límites de tamaño, tipo MIME validado y error 413/422 controlado.
- **Prueba de aceptación pendiente:** Archivos debajo/encima del límite, corruptos y formato no válido.
- **Responsable propuesto:** Integración + QA. **Estado de implementación:** pendiente; no se presume corregido.

### QA-01 — Pruebas históricas sin ejecución nueva vinculada al SHA

- **Severidad preliminar:** Media; **referencia:** Soportabilidad y fiabilidad FURPS+.
- **Evidencia:** [tests/:repositorio](https://github.com/Ronaldogh179/proyecto-licencias/blob/b81f5f2e0b1e2ff64d2d6535ff253b6e73498d88/tests/#L1). Informe de semana 12 describe 28 pruebas y 93 % de cobertura, pero son antecedentes no repetidos sobre el commit actual.
- **Riesgo:** No se acredita ausencia de regresiones en la instantánea auditada.
- **Plan:** Fijar dependencias, ejecutar pytest, pytest-cov, guardar comandos, entorno y salida.
- **Prueba de aceptación pendiente:** pytest -q; pytest --cov=src --cov-report=term-missing, resultados sin alterar.
- **Responsable propuesto:** QA. **Estado de implementación:** pendiente; no se presume corregido.

## Alcance, límites y evidencias

Las cifras históricas del Word de semana 12 (28 pruebas, 93 % cobertura, lotes de 600 y 1000) no se atribuyen a una nueva ejecución. Los paneles EV01–EV05 del ZIP son extractos visuales de líneas devueltas por la conexión de GitHub, **no capturas literales del navegador**. Se requieren pruebas dinámicas y capturas antes/después para cerrar estos hallazgos.
