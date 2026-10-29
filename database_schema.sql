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

-- =================================================================================
-- PMV 2: RAG NORMATIVO VECTORIAL, AUDITORÍA INTER-FOJAS Y DATA MASIVA
-- Historias: PMV2-1-HU06, PMV2-2-HU07 y PMV2-3-HU08
-- =================================================================================

-- 6. Tabla de Fragmentos Normativos Vectorizados (PMV2-1-HU06)
CREATE TABLE IF NOT EXISTS normativas_vectoriales (
    id_fragmento TEXT PRIMARY KEY,
    norma_origen VARCHAR(200) NOT NULL,
    articulo_inciso VARCHAR(200) NOT NULL,
    codigo_ciiu VARCHAR(10) NOT NULL,
    giro_comercial VARCHAR(80) NOT NULL,
    zona_urbana VARCHAR(20) NOT NULL,
    compatibilidad VARCHAR(40) NOT NULL,
    area_maxima_m2 NUMERIC(8,2) NOT NULL CHECK (area_maxima_m2 > 0),
    texto_fragmento_chunk TEXT NOT NULL,
    tokens_chunk INT DEFAULT 500 CHECK (tokens_chunk > 0),
    overlap_tokens INT DEFAULT 50 CHECK (overlap_tokens >= 0),
    embedding vector(16),
    fecha_indexacion TIMESTAMPTZ DEFAULT NOW()
);

-- Índice HNSW para búsqueda aproximada por similitud del coseno (pgvector)
CREATE INDEX IF NOT EXISTS idx_normativas_vectoriales_embedding_hnsw
    ON normativas_vectoriales
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_normativas_giro_zona
    ON normativas_vectoriales (giro_comercial, zona_urbana);

-- 7. Tabla de Dictámenes y Auditoría Cruzada PMV2 (PMV2-2-HU07 y PMV2-3-HU08)
CREATE TABLE IF NOT EXISTS dictamenes_auditoria (
    id_dictamen TEXT PRIMARY KEY,
    codigo_expediente VARCHAR(25) NOT NULL,
    giro_comercial VARCHAR(80) NOT NULL,
    zona_urbana VARCHAR(20) NOT NULL,
    similitud_coseno_rag NUMERIC(5,4) NOT NULL DEFAULT 0.0000,
    context_precision NUMERIC(5,4) NOT NULL DEFAULT 0.0000,
    compatibilidad_zonificacion VARCHAR(40) NOT NULL,
    cita_legal_exacta TEXT NOT NULL,
    texto_normativo_recuperado TEXT NOT NULL,
    dni_ruc_coincide BOOLEAN NOT NULL DEFAULT TRUE,
    area_coincide BOOLEAN NOT NULL DEFAULT TRUE,
    diferencia_area_m2 NUMERIC(8,2) NOT NULL DEFAULT 0.00,
    direccion_coincide BOOLEAN NOT NULL DEFAULT TRUE,
    total_discrepancias INT NOT NULL DEFAULT 0,
    alertas_detectadas JSONB NOT NULL DEFAULT '[]'::jsonb,
    es_conforme_cruce BOOLEAN NOT NULL DEFAULT TRUE,
    estado_auditoria_pmv2 VARCHAR(50) NOT NULL,
    pre_dictamen_explicable TEXT NOT NULL,
    latencia_rag_ms NUMERIC(8,2) NOT NULL DEFAULT 0.00,
    fecha_auditoria TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dictamenes_codigo_expediente
    ON dictamenes_auditoria (codigo_expediente);

CREATE INDEX IF NOT EXISTS idx_dictamenes_estado
    ON dictamenes_auditoria (estado_auditoria_pmv2);

-- 8. Procedimiento almacenado: indexar fragmento normativo con vector(16)
CREATE OR REPLACE FUNCTION sp_indexar_fragmento_normativo(
    p_id_fragmento TEXT,
    p_norma_origen TEXT,
    p_articulo_inciso TEXT,
    p_codigo_ciiu TEXT,
    p_giro_comercial TEXT,
    p_zona_urbana TEXT,
    p_compatibilidad TEXT,
    p_area_maxima_m2 NUMERIC,
    p_texto_fragmento_chunk TEXT,
    p_tokens_chunk INT DEFAULT 500,
    p_overlap_tokens INT DEFAULT 50,
    p_vector vector(16) DEFAULT NULL
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO normativas_vectoriales (
        id_fragmento, norma_origen, articulo_inciso, codigo_ciiu, giro_comercial,
        zona_urbana, compatibilidad, area_maxima_m2, texto_fragmento_chunk,
        tokens_chunk, overlap_tokens, embedding
    ) VALUES (
        p_id_fragmento, p_norma_origen, p_articulo_inciso, p_codigo_ciiu, p_giro_comercial,
        p_zona_urbana, p_compatibilidad, p_area_maxima_m2, p_texto_fragmento_chunk,
        p_tokens_chunk, p_overlap_tokens, p_vector
    )
    ON CONFLICT (id_fragmento) DO UPDATE SET
        norma_origen = EXCLUDED.norma_origen,
        articulo_inciso = EXCLUDED.articulo_inciso,
        codigo_ciiu = EXCLUDED.codigo_ciiu,
        giro_comercial = EXCLUDED.giro_comercial,
        zona_urbana = EXCLUDED.zona_urbana,
        compatibilidad = EXCLUDED.compatibilidad,
        area_maxima_m2 = EXCLUDED.area_maxima_m2,
        texto_fragmento_chunk = EXCLUDED.texto_fragmento_chunk,
        tokens_chunk = EXCLUDED.tokens_chunk,
        overlap_tokens = EXCLUDED.overlap_tokens,
        embedding = EXCLUDED.embedding,
        fecha_indexacion = NOW();

    RETURN p_id_fragmento;
END;
$$;

-- 9. Procedimiento almacenado: validar zonificación con similitud del coseno (HU07)
CREATE OR REPLACE FUNCTION sp_validar_zonificacion_rag_coseno(
    p_giro_comercial TEXT,
    p_zona_urbana TEXT,
    p_area_m2 NUMERIC
) RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    resultado JSONB;
BEGIN
    WITH vector_consulta AS (
        SELECT ARRAY[
            CASE WHEN lower(p_giro_comercial) = lower('Restaurante') THEN 1.0 ELSE 0.0 END,
            CASE WHEN lower(p_giro_comercial) = lower('Bodega') THEN 1.0 ELSE 0.0 END,
            CASE WHEN lower(p_giro_comercial) = lower('Oficina') THEN 1.0 ELSE 0.0 END,
            CASE WHEN lower(p_giro_comercial) = lower('Panaderia') THEN 1.0 ELSE 0.0 END,
            CASE WHEN lower(p_giro_comercial) = lower('Tienda') THEN 1.0 ELSE 0.0 END,
            CASE WHEN upper(p_zona_urbana) = 'CZ' THEN 1.0 ELSE 0.0 END,
            CASE WHEN upper(p_zona_urbana) = 'RDM' THEN 1.0 ELSE 0.0 END,
            CASE WHEN upper(p_zona_urbana) = 'CV' THEN 1.0 ELSE 0.0 END,
            CASE WHEN upper(p_zona_urbana) = 'I1' THEN 1.0 ELSE 0.0 END,
            CASE WHEN p_area_m2 > 0 THEN 0.1 ELSE 0.0 END,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]::vector(16) AS embedding
    )
    SELECT jsonb_build_object(
        'id_fragmento', n.id_fragmento,
        'norma_origen', n.norma_origen,
        'articulo_inciso', n.articulo_inciso,
        'codigo_ciiu', n.codigo_ciiu,
        'giro_comercial', n.giro_comercial,
        'zona_urbana', n.zona_urbana,
        'compatibilidad', n.compatibilidad,
        'area_maxima_m2', n.area_maxima_m2,
        'texto_fragmento_chunk', n.texto_fragmento_chunk,
        'similitud_coseno', ROUND((1 - (n.embedding <=> v.embedding))::numeric, 4),
        'compatible', (p_area_m2 <= n.area_maxima_m2 AND n.compatibilidad <> 'NO_COMPATIBLE'),
        'excede_area', (p_area_m2 > n.area_maxima_m2)
    )
    INTO resultado
    FROM normativas_vectoriales n, vector_consulta v
    WHERE lower(n.giro_comercial) = lower(p_giro_comercial)
      AND upper(n.zona_urbana) = upper(p_zona_urbana)
      AND n.embedding IS NOT NULL
    ORDER BY n.embedding <=> v.embedding
    LIMIT 1;

    IF resultado IS NULL THEN
        resultado := jsonb_build_object(
            'status', 'sin_coincidencia',
            'giro_comercial', p_giro_comercial,
            'zona_urbana', p_zona_urbana,
            'area_m2', p_area_m2,
            'compatible', FALSE,
            'similitud_coseno', 0.0
        );
    END IF;

    RETURN resultado;
END;
$$;

-- 10. Procedimiento almacenado: registrar auditoría cruzada PMV2 (HU07/HU08)
CREATE OR REPLACE FUNCTION sp_registrar_auditoria_cruzada_pmv2(
    p_id_dictamen TEXT,
    p_codigo_expediente TEXT,
    p_giro_comercial TEXT,
    p_zona_urbana TEXT,
    p_similitud_coseno_rag NUMERIC,
    p_context_precision NUMERIC,
    p_compatibilidad_zonificacion TEXT,
    p_cita_legal_exacta TEXT,
    p_texto_normativo_recuperado TEXT,
    p_dni_ruc_coincide BOOLEAN,
    p_area_coincide BOOLEAN,
    p_diferencia_area_m2 NUMERIC,
    p_direccion_coincide BOOLEAN,
    p_total_discrepancias INT,
    p_alertas_detectadas JSONB,
    p_es_conforme_cruce BOOLEAN,
    p_estado_auditoria_pmv2 TEXT,
    p_pre_dictamen_explicable TEXT,
    p_latencia_rag_ms NUMERIC
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO dictamenes_auditoria (
        id_dictamen, codigo_expediente, giro_comercial, zona_urbana,
        similitud_coseno_rag, context_precision, compatibilidad_zonificacion,
        cita_legal_exacta, texto_normativo_recuperado, dni_ruc_coincide,
        area_coincide, diferencia_area_m2, direccion_coincide, total_discrepancias,
        alertas_detectadas, es_conforme_cruce, estado_auditoria_pmv2,
        pre_dictamen_explicable, latencia_rag_ms
    ) VALUES (
        p_id_dictamen, p_codigo_expediente, p_giro_comercial, p_zona_urbana,
        p_similitud_coseno_rag, p_context_precision, p_compatibilidad_zonificacion,
        p_cita_legal_exacta, p_texto_normativo_recuperado, p_dni_ruc_coincide,
        p_area_coincide, p_diferencia_area_m2, p_direccion_coincide, p_total_discrepancias,
        p_alertas_detectadas, p_es_conforme_cruce, p_estado_auditoria_pmv2,
        p_pre_dictamen_explicable, p_latencia_rag_ms
    )
    ON CONFLICT (id_dictamen) DO UPDATE SET
        similitud_coseno_rag = EXCLUDED.similitud_coseno_rag,
        context_precision = EXCLUDED.context_precision,
        compatibilidad_zonificacion = EXCLUDED.compatibilidad_zonificacion,
        cita_legal_exacta = EXCLUDED.cita_legal_exacta,
        texto_normativo_recuperado = EXCLUDED.texto_normativo_recuperado,
        dni_ruc_coincide = EXCLUDED.dni_ruc_coincide,
        area_coincide = EXCLUDED.area_coincide,
        diferencia_area_m2 = EXCLUDED.diferencia_area_m2,
        direccion_coincide = EXCLUDED.direccion_coincide,
        total_discrepancias = EXCLUDED.total_discrepancias,
        alertas_detectadas = EXCLUDED.alertas_detectadas,
        es_conforme_cruce = EXCLUDED.es_conforme_cruce,
        estado_auditoria_pmv2 = EXCLUDED.estado_auditoria_pmv2,
        pre_dictamen_explicable = EXCLUDED.pre_dictamen_explicable,
        latencia_rag_ms = EXCLUDED.latencia_rag_ms,
        fecha_auditoria = NOW();

    RETURN p_id_dictamen;
END;
$$;

-- 11. Procedimiento almacenado: métricas consolidadas PMV1 + PMV2
CREATE OR REPLACE FUNCTION sp_obtener_metricas_pmv1_pmv2()
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    resultado JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_expedientes_pmv1', (SELECT COUNT(*) FROM expedientes),
        'total_auditorias_pmv2', (SELECT COUNT(*) FROM dictamenes_auditoria),
        'total_fragmentos_normativos', (SELECT COUNT(*) FROM normativas_vectoriales),
        'promedio_similitud_rag', COALESCE(
            (SELECT ROUND(AVG(similitud_coseno_rag)::numeric, 4) FROM dictamenes_auditoria), 0.0
        ),
        'promedio_context_precision', COALESCE(
            (SELECT ROUND(AVG(context_precision)::numeric, 4) FROM dictamenes_auditoria), 0.0
        ),
        'distribucion_riesgo_pmv1', COALESCE(
            (SELECT jsonb_object_agg(nivel_riesgo, total)
             FROM (SELECT nivel_riesgo, COUNT(*) AS total FROM expedientes GROUP BY nivel_riesgo) s),
            '{}'::jsonb
        ),
        'distribucion_estado_pmv2', COALESCE(
            (SELECT jsonb_object_agg(estado_auditoria_pmv2, total)
             FROM (SELECT estado_auditoria_pmv2, COUNT(*) AS total
                   FROM dictamenes_auditoria GROUP BY estado_auditoria_pmv2) s),
            '{}'::jsonb
        ),
        'fecha_calculo', NOW()
    ) INTO resultado;

    RETURN resultado;
END;
$$;
