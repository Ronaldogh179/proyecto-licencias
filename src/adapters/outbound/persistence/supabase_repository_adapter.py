import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from src.application.ports.output_ports import (
    AuditoriaPMV2RepositoryPort,
    ExpedienteRepositoryPort,
    UsuarioRepositoryPort,
)
from src.domain.entities.expediente import EvaluacionRiesgoDomain, Expediente
from src.domain.entities.normativa_rag import (
    DictamenAuditoriaPMV2Domain,
    FragmentoNormativoDomain,
    ResultadoCruceInterFojasDomain,
)
from src.domain.entities.usuario import Usuario

load_dotenv()


class InMemoryUsuarioRepository(UsuarioRepositoryPort):
    """Repositorio de usuarios institucionales para autenticación JWT (PMV1-1-HU01)."""

    def __init__(self) -> None:
        self._usuarios = {
            "evaluador@eltambo.gob.pe": Usuario(
                id_usuario="USR-TAMBO-001",
                nombre_completo="Ing. Simon Ronaldo Gonzales Jacinto",
                correo_institucional="evaluador@eltambo.gob.pe",
                password_hash="$2b$12$hash_simulado_seguro_ley29733",
                rol_operativo="EVALUADOR_LICENCIAS",
            ),
            "mesadepartes@eltambo.gob.pe": Usuario(
                id_usuario="USR-TAMBO-002",
                nombre_completo="Asist. Diego Uriol Ochoa Vilchez",
                correo_institucional="mesadepartes@eltambo.gob.pe",
                password_hash="$2b$12$hash_simulado_seguro_ley29733",
                rol_operativo="MESA_DE_PARTES",
            ),
        }

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        return self._usuarios.get(correo.strip().lower())


class HybridSupabaseExpedienteRepository(ExpedienteRepositoryPort, AuditoriaPMV2RepositoryPort):
    """PATRÓN REPOSITORY: sincroniza con Supabase Cloud y mantiene caché local de respaldo."""

    def __init__(self, db_path: str = "src/infrastructure/ml_artifacts/bd_expedientes_local.json") -> None:
        self._db_file = Path(db_path)
        self._db_file.parent.mkdir(parents=True, exist_ok=True)
        self._fragmentos_file = self._db_file.parent / "normativas_vectoriales_local.json"
        self._auditorias_file = self._db_file.parent / "dictamenes_auditoria_local.json"
        self._supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self._supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_KEY", "")
        self._expedientes: List[Expediente] = []
        self._fragmentos: List[FragmentoNormativoDomain] = []
        self._auditorias: List[DictamenAuditoriaPMV2Domain] = []
        self._cargar_semilla_o_archivo()
        self._cargar_fragmentos_y_auditorias()

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self._supabase_key,
            "Authorization": f"Bearer {self._supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }

    def _post_rpc(self, nombre_funcion: str, payload: Dict[str, Any], timeout: float = 3.5) -> Optional[Any]:
        if not self._supabase_url or not self._supabase_key:
            return None
        try:
            respuesta = httpx.post(
                f"{self._supabase_url}/rest/v1/rpc/{nombre_funcion}",
                json=payload,
                headers=self._headers,
                timeout=timeout,
            )
            if respuesta.status_code < 300:
                try:
                    return respuesta.json()
                except Exception:
                    return {"status": "ok"}
        except Exception:
            pass
        return None

    def _payload_expediente(self, expediente: Expediente) -> Dict[str, Any]:
        evaluacion = expediente.evaluacion_riesgo
        return {
            "codigo_expediente": expediente.codigo_expediente,
            "dni_ruc_titular_cifrado": expediente.dni_ruc_titular,
            "razon_social_nombre": expediente.razon_social_nombre,
            "giro_comercial": expediente.giro_comercial,
            "tipo_tramite": expediente.tipo_tramite,
            "direccion_predio": expediente.direccion_predio,
            "area_comercial_m2": expediente.area_comercial_m2,
            "documentos_faltantes": expediente.documentos_faltantes,
            "inconsistencias_detectadas": expediente.inconsistencias_detectadas,
            "documento_critico_faltante": expediente.documento_critico_faltante,
            "probabilidad_riesgo": evaluacion.probabilidad_riesgo if evaluacion else 0.0,
            "nivel_riesgo": evaluacion.nivel_riesgo if evaluacion else "BAJO",
            "estado_tramite": expediente.estado_tramite,
            "dias_habiles_transcurridos": expediente.dias_habiles_transcurridos,
        }

    def _sincronizar_a_supabase_cloud(self, expediente: Expediente) -> None:
        if not self._supabase_url or not self._supabase_key:
            return
        try:
            httpx.post(
                f"{self._supabase_url}/rest/v1/expedientes?on_conflict=codigo_expediente",
                json=self._payload_expediente(expediente),
                headers=self._headers,
                timeout=3.5,
            )
        except Exception:
            pass

    def _sincronizar_lote_a_supabase_cloud(self, expedientes: List[Expediente]) -> None:
        if not self._supabase_url or not self._supabase_key or not expedientes:
            return
        try:
            httpx.post(
                f"{self._supabase_url}/rest/v1/expedientes?on_conflict=codigo_expediente",
                json=[self._payload_expediente(expediente) for expediente in expedientes],
                headers=self._headers,
                timeout=8.0,
            )
        except Exception:
            pass

    def _cargar_semilla_o_archivo(self) -> None:
        if self._db_file.exists():
            try:
                raw = json.loads(self._db_file.read_text(encoding="utf-8"))
                self._expedientes = []
                for item in raw:
                    evaluacion = item.get("evaluacion_riesgo")
                    evaluacion_obj = EvaluacionRiesgoDomain(**evaluacion) if evaluacion else None
                    item_copy = {k: v for k, v in item.items() if k != "evaluacion_riesgo"}
                    self._expedientes.append(
                        Expediente(**item_copy, evaluacion_riesgo=evaluacion_obj)
                    )
                if self._expedientes:
                    return
            except Exception:
                pass

        semillas = [
            Expediente(
                id_expediente="a101-eltambo-2026",
                codigo_expediente="EXP-2026-0348",
                dni_ruc_titular="20609845121",
                razon_social_nombre="Inversiones Gastronómicas El Mantaro S.A.C.",
                giro_comercial="Restaurante",
                tipo_tramite="Nueva licencia",
                direccion_predio="Av. Mariscal Castilla N.° 1420 - El Tambo",
                area_comercial_m2=125.0,
                nombre_archivo_pdf="exp_2026_0348_restaurante.pdf",
                documentos_faltantes=2,
                inconsistencias_detectadas=2,
                documento_critico_faltante=1,
                texto_extraido_resumen="Formulario TUPA sin firma de arquitecto en plano de distribución ni Certificado ITSE.",
                confianza_ocr=95.4,
                tiempo_ocr_seg=0.41,
                estado_tramite="OBSERVABLE_PRIORITARIO",
                dias_habiles_transcurridos=2,
                evaluacion_riesgo=EvaluacionRiesgoDomain(
                    algoritmo_empleado="XGBoostClassifier (F1=0.925 | Recall=96.9%)",
                    resultado_observacion=1,
                    probabilidad_riesgo=0.9420,
                    nivel_riesgo="ALTO",
                    importancia_variables={"documento_critico_faltante": 0.46, "documentos_faltantes": 0.29},
                    latencia_inferencia_ms=1.15,
                ),
            ),
            Expediente(
                id_expediente="a102-eltambo-2026",
                codigo_expediente="EXP-2026-0349",
                dni_ruc_titular="10458932147",
                razon_social_nombre="Panificadora San Antonio de Huancayo E.I.R.L.",
                giro_comercial="Panaderia",
                tipo_tramite="Modificacion",
                direccion_predio="Jr. Parra del Riego N.° 640 - El Tambo",
                area_comercial_m2=78.5,
                nombre_archivo_pdf="exp_2026_0349_panaderia.pdf",
                documentos_faltantes=1,
                inconsistencias_detectadas=2,
                documento_critico_faltante=0,
                texto_extraido_resumen="Discrepancia menor en metraje cuadrado declarado en croquis interno.",
                confianza_ocr=96.1,
                tiempo_ocr_seg=0.38,
                estado_tramite="OBSERVABLE_PRIORITARIO",
                dias_habiles_transcurridos=3,
                evaluacion_riesgo=EvaluacionRiesgoDomain(
                    algoritmo_empleado="XGBoostClassifier (F1=0.925 | Recall=96.9%)",
                    resultado_observacion=1,
                    probabilidad_riesgo=0.6150,
                    nivel_riesgo="MEDIO",
                    importancia_variables={"documento_critico_faltante": 0.46, "documentos_faltantes": 0.29},
                    latencia_inferencia_ms=1.08,
                ),
            ),
            Expediente(
                id_expediente="a103-eltambo-2026",
                codigo_expediente="EXP-2026-0350",
                dni_ruc_titular="10728491023",
                razon_social_nombre="Bodega Multiservicios Los Andes",
                giro_comercial="Bodega",
                tipo_tramite="Renovacion",
                direccion_predio="Jr. Arequipa N.° 890 - El Tambo",
                area_comercial_m2=42.0,
                nombre_archivo_pdf="exp_2026_0350_bodega.pdf",
                documentos_faltantes=0,
                inconsistencias_detectadas=0,
                documento_critico_faltante=0,
                texto_extraido_resumen="Requisitos TUPA completos. DNI, RUC y Declaración Jurada firmados conforme.",
                confianza_ocr=98.2,
                tiempo_ocr_seg=0.29,
                estado_tramite="PRE_CONFORME",
                dias_habiles_transcurridos=1,
                evaluacion_riesgo=EvaluacionRiesgoDomain(
                    algoritmo_empleado="XGBoostClassifier (F1=0.925 | Recall=96.9%)",
                    resultado_observacion=0,
                    probabilidad_riesgo=0.0840,
                    nivel_riesgo="BAJO",
                    importancia_variables={"documento_critico_faltante": 0.46, "documentos_faltantes": 0.29},
                    latencia_inferencia_ms=0.95,
                ),
            ),
        ]
        self._expedientes = semillas
        self._persistir_en_disco()

    def _cargar_fragmentos_y_auditorias(self) -> None:
        if self._fragmentos_file.exists():
            try:
                raw = json.loads(self._fragmentos_file.read_text(encoding="utf-8"))
                self._fragmentos = [FragmentoNormativoDomain(**item) for item in raw]
            except Exception:
                self._fragmentos = []

        if self._auditorias_file.exists():
            try:
                raw = json.loads(self._auditorias_file.read_text(encoding="utf-8"))
                self._auditorias = []
                for item in raw:
                    cruce = item.get("resultado_cruce")
                    cruce_obj = (
                        ResultadoCruceInterFojasDomain(**cruce)
                        if isinstance(cruce, dict)
                        else cruce
                    )
                    item_copy = {k: v for k, v in item.items() if k != "resultado_cruce"}
                    self._auditorias.append(
                        DictamenAuditoriaPMV2Domain(**item_copy, resultado_cruce=cruce_obj)
                    )
            except Exception:
                self._auditorias = []

    def _persistir_en_disco(self) -> None:
        data = [asdict(expediente) for expediente in self._expedientes]
        self._db_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _persistir_fragmentos_en_disco(self) -> None:
        data = [asdict(fragmento) for fragmento in self._fragmentos]
        self._fragmentos_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _persistir_auditorias_en_disco(self) -> None:
        data = [asdict(dictamen) for dictamen in self._auditorias]
        self._auditorias_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def guardar_expediente(self, expediente: Expediente) -> Expediente:
        self._expedientes = [
            e for e in self._expedientes if e.codigo_expediente != expediente.codigo_expediente
        ]
        self._expedientes.append(expediente)
        self._persistir_en_disco()
        self._sincronizar_a_supabase_cloud(expediente)
        return expediente

    def guardar_lote_expedientes(self, expedientes: List[Expediente]) -> int:
        mapa = {expediente.codigo_expediente: expediente for expediente in self._expedientes}
        for expediente in expedientes:
            mapa[expediente.codigo_expediente] = expediente
        self._expedientes = list(mapa.values())
        self._persistir_en_disco()
        self._sincronizar_lote_a_supabase_cloud(expedientes)
        return len(expedientes)

    def listar_todos_priorizados(self) -> List[Expediente]:
        return sorted(
            self._expedientes,
            key=lambda x: x.evaluacion_riesgo.probabilidad_riesgo if x.evaluacion_riesgo else 0.0,
            reverse=True,
        )

    def obtener_por_codigo(self, codigo_expediente: str) -> Optional[Expediente]:
        for expediente in self._expedientes:
            if expediente.codigo_expediente == codigo_expediente.strip().upper():
                return expediente
        return None

    def guardar_fragmento_normativo(
        self,
        fragmento: FragmentoNormativoDomain,
        vector_embedding: Optional[List[float]] = None,
    ) -> FragmentoNormativoDomain:
        self._fragmentos = [
            existente
            for existente in self._fragmentos
            if existente.id_fragmento != fragmento.id_fragmento
        ]
        self._fragmentos.append(fragmento)
        self._persistir_fragmentos_en_disco()

        vector_pg = None
        if vector_embedding is not None:
            vector_pg = "[" + ",".join(str(float(valor)) for valor in vector_embedding) + "]"

        payload = {
            "p_id_fragmento": fragmento.id_fragmento,
            "p_norma_origen": fragmento.norma_origen,
            "p_articulo_inciso": fragmento.articulo_inciso,
            "p_codigo_ciiu": fragmento.codigo_ciiu,
            "p_giro_comercial": fragmento.giro_comercial,
            "p_zona_urbana": fragmento.zona_urbana,
            "p_compatibilidad": fragmento.compatibilidad,
            "p_area_maxima_m2": fragmento.area_maxima_m2,
            "p_texto_fragmento_chunk": fragmento.texto_fragmento_chunk,
            "p_tokens_chunk": fragmento.tokens_chunk,
            "p_overlap_tokens": fragmento.overlap_tokens,
            "p_vector": vector_pg,
        }
        self._post_rpc("sp_indexar_fragmento_normativo", payload)
        return fragmento

    def listar_fragmentos_normativos(self) -> List[FragmentoNormativoDomain]:
        return list(self._fragmentos)

    def _payload_dictamen_tabla(self, dictamen: DictamenAuditoriaPMV2Domain) -> Dict[str, Any]:
        return {
            "id_dictamen": dictamen.id_dictamen,
            "codigo_expediente": dictamen.codigo_expediente,
            "giro_comercial": dictamen.giro_comercial,
            "zona_urbana": dictamen.zona_urbana,
            "similitud_coseno_rag": dictamen.similitud_coseno_rag,
            "context_precision": dictamen.context_precision,
            "compatibilidad_zonificacion": dictamen.compatibilidad_zonificacion,
            "cita_legal_exacta": dictamen.cita_legal_exacta,
            "texto_normativo_recuperado": dictamen.texto_normativo_recuperado,
            "dni_ruc_coincide": dictamen.resultado_cruce.dni_ruc_coincide,
            "area_coincide": dictamen.resultado_cruce.area_coincide,
            "diferencia_area_m2": dictamen.resultado_cruce.diferencia_area_m2,
            "direccion_coincide": dictamen.resultado_cruce.direccion_coincide,
            "total_discrepancias": dictamen.resultado_cruce.total_discrepancias,
            "alertas_detectadas": dictamen.resultado_cruce.alertas_detectadas,
            "es_conforme_cruce": dictamen.resultado_cruce.es_conforme_cruce,
            "estado_auditoria_pmv2": dictamen.estado_auditoria_pmv2,
            "pre_dictamen_explicable": dictamen.pre_dictamen_explicable,
            "latencia_rag_ms": dictamen.latencia_rag_ms,
        }

    def _payload_dictamen_rpc(self, dictamen: DictamenAuditoriaPMV2Domain) -> Dict[str, Any]:
        payload_tabla = self._payload_dictamen_tabla(dictamen)
        return {f"p_{clave}": valor for clave, valor in payload_tabla.items()}

    def guardar_auditoria_pmv2(
        self,
        dictamen: DictamenAuditoriaPMV2Domain,
    ) -> DictamenAuditoriaPMV2Domain:
        self._auditorias = [
            existente
            for existente in self._auditorias
            if existente.id_dictamen != dictamen.id_dictamen
        ]
        self._auditorias.append(dictamen)
        self._persistir_auditorias_en_disco()
        self.registrar_auditoria_cruzada_pmv2(dictamen)
        return dictamen

    def guardar_lote_auditorias_pmv2(
        self,
        dictamenes: List[DictamenAuditoriaPMV2Domain],
    ) -> int:
        mapa = {dictamen.id_dictamen: dictamen for dictamen in self._auditorias}
        for dictamen in dictamenes:
            mapa[dictamen.id_dictamen] = dictamen
        self._auditorias = list(mapa.values())
        self._persistir_auditorias_en_disco()

        if self._supabase_url and self._supabase_key and dictamenes:
            try:
                httpx.post(
                    f"{self._supabase_url}/rest/v1/dictamenes_auditoria?on_conflict=id_dictamen",
                    json=[self._payload_dictamen_tabla(dictamen) for dictamen in dictamenes],
                    headers=self._headers,
                    timeout=8.0,
                )
            except Exception:
                pass
        return len(dictamenes)

    def listar_auditorias_pmv2(self) -> List[DictamenAuditoriaPMV2Domain]:
        return list(self._auditorias)

    def validar_zonificacion_rag_coseno(
        self,
        giro_comercial: str,
        zona_urbana: str,
        area_m2: float,
    ) -> Dict[str, Any]:
        payload = {
            "p_giro_comercial": giro_comercial,
            "p_zona_urbana": zona_urbana,
            "p_area_m2": area_m2,
        }
        respuesta_rpc = self._post_rpc("sp_validar_zonificacion_rag_coseno", payload)
        if isinstance(respuesta_rpc, dict):
            respuesta_rpc.setdefault("fuente", "supabase_rpc")
            return respuesta_rpc

        for fragmento in self._fragmentos:
            if (
                fragmento.giro_comercial.strip().lower() == giro_comercial.strip().lower()
                and fragmento.zona_urbana.strip().upper() == zona_urbana.strip().upper()
            ):
                return {
                    "status": "ok",
                    "fuente": "cache_local",
                    "id_fragmento": fragmento.id_fragmento,
                    "compatibilidad": fragmento.compatibilidad,
                    "area_maxima_m2": fragmento.area_maxima_m2,
                    "excede_area": float(area_m2) > float(fragmento.area_maxima_m2),
                    "compatible": (
                        float(area_m2) <= float(fragmento.area_maxima_m2)
                        and fragmento.compatibilidad != "NO_COMPATIBLE"
                    ),
                    "similitud_coseno": fragmento.similitud_coseno,
                }

        return {
            "status": "sin_coincidencia",
            "fuente": "cache_local",
            "giro_comercial": giro_comercial,
            "zona_urbana": zona_urbana,
            "area_m2": area_m2,
            "compatible": False,
        }

    def registrar_auditoria_cruzada_pmv2(
        self,
        dictamen: DictamenAuditoriaPMV2Domain,
    ) -> Dict[str, Any]:
        respuesta_rpc = self._post_rpc(
            "sp_registrar_auditoria_cruzada_pmv2",
            self._payload_dictamen_rpc(dictamen),
        )
        if isinstance(respuesta_rpc, dict):
            respuesta_rpc.setdefault("status", "ok")
            respuesta_rpc.setdefault("fuente", "supabase_rpc")
            return respuesta_rpc
        return {
            "status": "ok",
            "fuente": "cache_local",
            "id_dictamen": dictamen.id_dictamen,
        }

    def obtener_metricas_pmv1_pmv2(self) -> Dict[str, Any]:
        distribucion_riesgo: Dict[str, int] = {}
        for expediente in self._expedientes:
            nivel = expediente.evaluacion_riesgo.nivel_riesgo if expediente.evaluacion_riesgo else "BAJO"
            distribucion_riesgo[nivel] = distribucion_riesgo.get(nivel, 0) + 1

        distribucion_pmv2: Dict[str, int] = {}
        suma_similitud = 0.0
        suma_context = 0.0
        for dictamen in self._auditorias:
            estado = dictamen.estado_auditoria_pmv2
            distribucion_pmv2[estado] = distribucion_pmv2.get(estado, 0) + 1
            suma_similitud += dictamen.similitud_coseno_rag
            suma_context += dictamen.context_precision

        total_auditorias = len(self._auditorias)
        metricas_locales: Dict[str, Any] = {
            "fuente": "cache_local",
            "total_expedientes_pmv1": len(self._expedientes),
            "total_auditorias_pmv2": total_auditorias,
            "total_fragmentos_normativos": len(self._fragmentos),
            "promedio_similitud_rag": (
                round(suma_similitud / total_auditorias, 4) if total_auditorias else 0.0
            ),
            "promedio_context_precision": (
                round(suma_context / total_auditorias, 4) if total_auditorias else 0.0
            ),
            "distribucion_riesgo_pmv1": distribucion_riesgo,
            "distribucion_estado_pmv2": distribucion_pmv2,
        }

        respuesta_rpc = self._post_rpc("sp_obtener_metricas_pmv1_pmv2", {})
        if isinstance(respuesta_rpc, dict):
            for clave, valor in metricas_locales.items():
                if clave != "fuente":
                    respuesta_rpc.setdefault(clave, valor)
            respuesta_rpc.setdefault("fuente", "supabase_rpc")
            return respuesta_rpc
        return metricas_locales

    def ejecutar_carga_masiva_expedientes(self, cantidad: int) -> Dict[str, Any]:
        return {
            "cantidad_solicitada": cantidad,
            "total_expedientes_persistidos": len(self._expedientes),
            "total_auditorias_persistidas": len(self._auditorias),
            "total_fragmentos_normativos": len(self._fragmentos),
            "modo_persistencia": (
                "supabase_cloud+local_cache"
                if self._supabase_url and self._supabase_key
                else "local_cache"
            ),
            "fuente": "cache_local",
        }
