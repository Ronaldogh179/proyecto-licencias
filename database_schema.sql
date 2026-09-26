-- =================================================================================
-- SIMEL - MUNICIPALIDAD DISTRITAL DE EL TAMBO (JUNÍN, PERÚ)
-- ESQUEMA FÍSICO HÍBRIDO (RELACIONAL + VECTORIAL) - CUMPLIMIENTO LEY N.° 29733 y 28976
-- =================================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Tabla de Funcionarios Municipales (PMV1-1-HU01)
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_completo VARCHAR(120) NOT NULL,
    correo_institucional VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol_operativo VARCHAR(30) NOT NULL CHECK (rol_operativo IN ('MESA_DE_PARTES', 'EVALUADOR_LICENCIAS', 'ADMIN_TI')),
    estado_activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tabla Central de Expedientes TUPA (PMV1-2-HU02 y PMV1-5-HU05)
CREATE TABLE IF NOT EXISTS expedientes (
    id_expediente UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_expediente VARCHAR(25) UNIQUE NOT NULL,
    dni_ruc_titular_cifrado VARCHAR(255) NOT NULL,
    razon_social_nombre VARCHAR(150) NOT NULL,
    giro_comercial VARCHAR(50) NOT NULL,
    tipo_tramite VARCHAR(40) NOT NULL,
    direccion_predio VARCHAR(200) NOT NULL,
    area_comercial_m2 NUMERIC(8,2) NOT NULL CHECK (area_comercial_m2 > 0),
    documentos_faltantes INT DEFAULT 0 CHECK (documentos_faltantes BETWEEN 0 AND 3),
    inconsistencias_detectadas INT DEFAULT 0 CHECK (inconsistencias_detectadas BETWEEN 0 AND 3),
    documento_critico_faltante INT DEFAULT 0 CHECK (documento_critico_faltante IN (0, 1)),
    probabilidad_riesgo NUMERIC(5,4) DEFAULT 0.0000,
    nivel_riesgo VARCHAR(15) DEFAULT 'BAJO' CHECK (nivel_riesgo IN ('ALTO', 'MEDIO', 'BAJO')),
    estado_tramite VARCHAR(30) DEFAULT 'INGRESADO',
    dias_habiles_transcurridos INT DEFAULT 1,
    fecha_ingreso TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabla de Extracciones Ópticas OCR (PMV1-3-HU03)
CREATE TABLE IF NOT EXISTS extracciones_ocr (
    id_extraccion UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_expediente UUID UNIQUE REFERENCES expedientes(id_expediente) ON DELETE CASCADE,
    motor_utilizado VARCHAR(60) DEFAULT 'PyMuPDF + Tesseract OCR',
    texto_resumen TEXT,
    confianza_promedio_ocr NUMERIC(5,2) DEFAULT 96.80,
    tiempo_extraccion_seg NUMERIC(6,3) DEFAULT 0.050,
    fecha_procesamiento TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tabla de Predicciones de Machine Learning (PMV1-4-HU04)
CREATE TABLE IF NOT EXISTS predicciones_ml (
    id_prediccion UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_expediente UUID REFERENCES expedientes(id_expediente) ON DELETE CASCADE,
    algoritmo_empleado VARCHAR(60) NOT NULL,
    resultado_observacion INT NOT NULL CHECK (resultado_observacion IN (0, 1)),
    probabilidad_riesgo NUMERIC(5,4) NOT NULL,
    nivel_riesgo VARCHAR(15) NOT NULL,
    latencia_inferencia_ms NUMERIC(6,2) NOT NULL,
    fecha_prediccion TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Semilla inicial de datos reales para validación en Supabase
INSERT INTO usuarios (nombre_completo, correo_institucional, password_hash, rol_operativo)
VALUES
('Ing. Simon Ronaldo Gonzales Jacinto', 'evaluador@eltambo.gob.pe', '$2b$12$hash_municipal_seguro_2026', 'EVALUADOR_LICENCIAS'),
('Asist. Diego Uriol Ochoa Vilchez', 'mesadepartes@eltambo.gob.pe', '$2b$12$hash_municipal_seguro_2026', 'MESA_DE_PARTES')
ON CONFLICT (correo_institucional) DO NOTHING;

INSERT INTO expedientes (codigo_expediente, dni_ruc_titular_cifrado, razon_social_nombre, giro_comercial, tipo_tramite, direccion_predio, area_comercial_m2, documentos_faltantes, inconsistencias_detectadas, documento_critico_faltante, probabilidad_riesgo, nivel_riesgo, estado_tramite, dias_habiles_transcurridos)
VALUES
('EXP-2026-0348', '20609845121', 'Inversiones Gastronómicas El Mantaro S.A.C.', 'Restaurante', 'Nueva licencia', 'Av. Mariscal Castilla N.° 1420 - El Tambo', 125.00, 2, 2, 1, 0.9420, 'ALTO', 'OBSERVABLE_PRIORITARIO', 2),
('EXP-2026-0351', '20601122334', 'Restaurante Turístico El Huaytapallana S.A.C.', 'Restaurante', 'Nueva licencia', 'Av. Huancavelica N.° 1050 - El Tambo', 110.50, 2, 1, 1, 0.9180, 'ALTO', 'OBSERVABLE_PRIORITARIO', 1),
('EXP-2026-0349', '10458932147', 'Panificadora San Antonio de Huancayo E.I.R.L.', 'Panaderia', 'Modificacion', 'Jr. Parra del Riego N.° 640 - El Tambo', 78.50, 1, 2, 0, 0.6150, 'MEDIO', 'OBSERVABLE_PRIORITARIO', 3),
('EXP-2026-0350', '10728491023', 'Bodega Multiservicios Los Andes', 'Bodega', 'Renovacion', 'Jr. Arequipa N.° 890 - El Tambo', 42.00, 0, 0, 0, 0.0840, 'BAJO', 'PRE_CONFORME', 1)
ON CONFLICT (codigo_expediente) DO NOTHING;
