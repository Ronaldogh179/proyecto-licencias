-- SIMEL El Tambo v3.0.0 | Migración incremental de PMV3
-- Ejecutar el archivo completo en el SQL Editor del proyecto Supabase de SIMEL.
-- Requiere las tablas existentes public.expedientes y public.dictamenes_auditoria.
-- El bloque incluye la comprobación final y no carga expedientes ni usuarios.
BEGIN;

DO $preflight$
DECLARE
    tipo_estado text;
    largo_estado integer;
    collation_estado text;
    largo_requerido constant integer := length('RECHAZADO_IMPROCEDENTE_ZONIFICACION');
BEGIN
    SELECT data_type, character_maximum_length, collation_name
    INTO tipo_estado, largo_estado, collation_estado
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'expedientes'
      AND column_name = 'estado_tramite'
      AND domain_name IS NULL;

    IF tipo_estado IS NULL OR tipo_estado NOT IN ('text', 'character varying') THEN
        RAISE EXCEPTION 'Tipo inesperado en public.expedientes.estado_tramite: %',
            coalesce(tipo_estado, 'columna ausente o definida mediante un dominio');
    END IF;

    -- Solo se amplía un VARCHAR si el estado completo no cabe.
    IF tipo_estado = 'character varying' AND largo_estado < largo_requerido THEN
        IF collation_estado IS NOT NULL THEN
            RAISE EXCEPTION 'estado_tramite tiene una intercalación personalizada; revisar antes de ampliar el campo';
        END IF;

        ALTER TABLE public.expedientes
            ALTER COLUMN estado_tramite TYPE VARCHAR(35);
    END IF;

    -- La RPC SECURITY INVOKER usa los permisos existentes del backend.
    IF NOT has_table_privilege('service_role', 'public.expedientes', 'SELECT')
       OR NOT has_table_privilege('service_role', 'public.expedientes', 'UPDATE')
       OR NOT has_table_privilege('service_role', 'public.dictamenes_auditoria', 'SELECT')
       OR NOT has_table_privilege('service_role', 'public.dictamenes_auditoria', 'UPDATE') THEN
        RAISE EXCEPTION 'service_role requiere SELECT y UPDATE en public.expedientes y public.dictamenes_auditoria';
    END IF;
END;
$preflight$;

ALTER TABLE public.dictamenes_auditoria
    ADD COLUMN IF NOT EXISTS decision_final_humano VARCHAR(50) DEFAULT 'PENDIENTE_REVISION_HITL',
    ADD COLUMN IF NOT EXISTS funcionario_evaluador_firma VARCHAR(150) DEFAULT '',
    ADD COLUMN IF NOT EXISTS observaciones_funcionario_hitl TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS iteraciones_grafo INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS temperatura_llm NUMERIC(4,2) DEFAULT 0.10,
    ADD COLUMN IF NOT EXISTS fecha_resolucion_hitl TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS public.predictamenes_pmv3 (
    id_predictamen TEXT PRIMARY KEY,
    id_expediente TEXT NOT NULL,
    codigo_expediente VARCHAR(25) UNIQUE NOT NULL,
    razon_social_nombre VARCHAR(150) NOT NULL,
    giro_comercial VARCHAR(80) NOT NULL,
    zona_urbana VARCHAR(20) NOT NULL,
    area_comercial_m2 NUMERIC(8,2) NOT NULL,
    probabilidad_riesgo_ml NUMERIC(5,4) NOT NULL,
    nivel_riesgo_ml VARCHAR(15) NOT NULL,
    similitud_coseno_rag NUMERIC(5,4) NOT NULL,
    context_precision_rag NUMERIC(5,4) NOT NULL,
    compatibilidad_zonificacion VARCHAR(40) NOT NULL,
    es_conforme_interfojas BOOLEAN NOT NULL DEFAULT TRUE,
    total_discrepancias_interfojas INT NOT NULL DEFAULT 0,
    temperatura_llm NUMERIC(4,2) NOT NULL DEFAULT 0.10,
    iteraciones_grafo INT NOT NULL DEFAULT 1,
    alucinaciones_detectadas INT NOT NULL DEFAULT 0,
    recomendacion_ia VARCHAR(50) NOT NULL,
    cita_legal_consolidada TEXT NOT NULL,
    texto_predictamen_explicable TEXT NOT NULL,
    dias_habiles_transcurridos INT NOT NULL DEFAULT 1,
    dias_restantes_sla INT NOT NULL DEFAULT 7,
    estado_semaforo_sla VARCHAR(40) NOT NULL,
    cumple_sla_legal BOOLEAN NOT NULL DEFAULT TRUE,
    decision_final_humano VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE_REVISION_HITL',
    funcionario_evaluador_firma VARCHAR(150) DEFAULT '',
    observaciones_funcionario_hitl TEXT DEFAULT '',
    fecha_generacion_ia TIMESTAMPTZ DEFAULT NOW(),
    fecha_resolucion_hitl TIMESTAMPTZ,
    latencia_total_grafo_ms NUMERIC(10,3) DEFAULT 0.000,
    nodos_ejecutados JSONB NOT NULL DEFAULT '[]'::jsonb,
    tipo_importancia_xai VARCHAR(80) DEFAULT 'global_feature_importance_xgboost',
    context_precision_rag_tipo VARCHAR(80) DEFAULT 'heuristica_experimental_derivada_de_similitud_coseno',
    motor_tipo VARCHAR(50) DEFAULT 'determinista_sin_llm',
    alucinaciones_detectadas_no_aplica BOOLEAN DEFAULT TRUE
);

ALTER TABLE public.predictamenes_pmv3
    ADD COLUMN IF NOT EXISTS id_expediente TEXT,
    ADD COLUMN IF NOT EXISTS nodos_ejecutados JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS tipo_importancia_xai VARCHAR(80) DEFAULT 'global_feature_importance_xgboost',
    ADD COLUMN IF NOT EXISTS context_precision_rag_tipo VARCHAR(80) DEFAULT 'heuristica_experimental_derivada_de_similitud_coseno',
    ADD COLUMN IF NOT EXISTS motor_tipo VARCHAR(50) DEFAULT 'determinista_sin_llm',
    ADD COLUMN IF NOT EXISTS alucinaciones_detectadas_no_aplica BOOLEAN DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_predictamenes_pmv3_codigo
    ON public.predictamenes_pmv3 (codigo_expediente);

ALTER TABLE public.predictamenes_pmv3 ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pmd_pmv3_service_role_all ON public.predictamenes_pmv3;
CREATE POLICY pmd_pmv3_service_role_all
    ON public.predictamenes_pmv3
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE OR REPLACE FUNCTION public.sp_registrar_resolucion_hitl_pmv3(
    p_codigo_expediente TEXT,
    p_decision_final_humano TEXT,
    p_funcionario_evaluador_firma TEXT,
    p_observaciones_funcionario_hitl TEXT,
    p_fecha_resolucion_hitl TIMESTAMPTZ
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, public, pg_temp
AS $hitl$
DECLARE
    nuevo_estado TEXT;
BEGIN
    IF p_decision_final_humano IS NULL
       OR p_decision_final_humano NOT IN ('APROBADO_HITL', 'OBSERVADO_HITL', 'RECHAZADO_HITL') THEN
        RAISE EXCEPTION 'Decisión HITL inválida: %', p_decision_final_humano
            USING ERRCODE = '22023';
    END IF;

    nuevo_estado := CASE p_decision_final_humano
        WHEN 'APROBADO_HITL' THEN 'APROBADO_CON_LICENCIA'
        WHEN 'OBSERVADO_HITL' THEN 'OBSERVADO_NOTIFICADO_HITL'
        ELSE 'RECHAZADO_IMPROCEDENTE_ZONIFICACION'
    END;

    UPDATE public.predictamenes_pmv3
    SET decision_final_humano = p_decision_final_humano,
        funcionario_evaluador_firma = p_funcionario_evaluador_firma,
        observaciones_funcionario_hitl = p_observaciones_funcionario_hitl,
        fecha_resolucion_hitl = p_fecha_resolucion_hitl
    WHERE codigo_expediente = p_codigo_expediente;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Falta el predictamen PMV3 indispensable para %', p_codigo_expediente
            USING ERRCODE = 'P0002';
    END IF;

    UPDATE public.dictamenes_auditoria
    SET decision_final_humano = p_decision_final_humano,
        funcionario_evaluador_firma = p_funcionario_evaluador_firma,
        observaciones_funcionario_hitl = p_observaciones_funcionario_hitl,
        fecha_resolucion_hitl = p_fecha_resolucion_hitl
    WHERE codigo_expediente = p_codigo_expediente;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Falta el dictamen PMV2 indispensable para %', p_codigo_expediente
            USING ERRCODE = 'P0002';
    END IF;

    UPDATE public.expedientes
    SET estado_tramite = nuevo_estado
    WHERE codigo_expediente = p_codigo_expediente;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Falta el expediente indispensable para %', p_codigo_expediente
            USING ERRCODE = 'P0002';
    END IF;

    RETURN jsonb_build_object(
        'status', 'ok',
        'codigo_expediente', p_codigo_expediente,
        'decision_final_humano', p_decision_final_humano,
        'estado_expediente', nuevo_estado,
        'funcionario_evaluador_firma', p_funcionario_evaluador_firma,
        'fecha_resolucion_hitl', p_fecha_resolucion_hitl
    );
END;
$hitl$;

REVOKE ALL ON TABLE public.predictamenes_pmv3 FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.sp_registrar_resolucion_hitl_pmv3(TEXT, TEXT, TEXT, TEXT, TIMESTAMPTZ)
    FROM PUBLIC, anon, authenticated;

GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.predictamenes_pmv3 TO service_role;
GRANT EXECUTE ON FUNCTION public.sp_registrar_resolucion_hitl_pmv3(TEXT, TEXT, TEXT, TEXT, TIMESTAMPTZ)
    TO service_role;

NOTIFY pgrst, 'reload schema';
COMMIT;

-- Resultado esperado: tabla y RPC presentes, RLS activo, seis columnas HITL
-- y true en permisos_backend_ok y acceso_directo_bloqueado.
WITH objetos AS (
    SELECT
        'public.predictamenes_pmv3'::regclass AS tabla,
        'public.sp_registrar_resolucion_hitl_pmv3(text,text,text,text,timestamptz)'::regprocedure AS rpc
)
SELECT
    objetos.tabla AS tabla_pmv3,
    objetos.rpc AS rpc_hitl,
    pg_class.relrowsecurity AS rls_activo,
    (SELECT count(*)
     FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'dictamenes_auditoria'
       AND column_name IN (
           'decision_final_humano',
           'funcionario_evaluador_firma',
           'observaciones_funcionario_hitl',
           'iteraciones_grafo',
           'temperatura_llm',
           'fecha_resolucion_hitl'
       )) AS columnas_hitl_dictamen,
    (has_table_privilege('service_role', objetos.tabla, 'SELECT')
     AND has_table_privilege('service_role', objetos.tabla, 'INSERT')
     AND has_table_privilege('service_role', objetos.tabla, 'UPDATE')
     AND has_function_privilege('service_role', objetos.rpc, 'EXECUTE')) AS permisos_backend_ok,
    NOT EXISTS (
        SELECT 1
        FROM (VALUES ('anon'), ('authenticated')) AS roles(rol)
        WHERE has_table_privilege(roles.rol, objetos.tabla, 'SELECT,INSERT,UPDATE,DELETE')
           OR has_function_privilege(roles.rol, objetos.rpc, 'EXECUTE')
    ) AS acceso_directo_bloqueado
FROM objetos
JOIN pg_class ON pg_class.oid = objetos.tabla;
