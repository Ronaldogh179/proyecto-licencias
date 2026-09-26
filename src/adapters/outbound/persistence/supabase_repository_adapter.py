import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from src.application.ports.output_ports import ExpedienteRepositoryPort, UsuarioRepositoryPort
from src.domain.entities.expediente import EvaluacionRiesgoDomain, Expediente
from src.domain.entities.usuario import Usuario

class HybridSupabaseExpedienteRepository(ExpedienteRepositoryPort):
    """PATRÓN REPOSITORY: Persistencia híbrida en Supabase Cloud + Respaldo JSON/Memoria."""

    def __init__(self) -> None:
        self._storage_file = Path("src/infrastructure/ml_artifacts/bd_expedientes_local.json")
        self._expedientes: Dict[str, Expediente] = {}
        self._supabase_client = None

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if url and key:
            try:
                from supabase import create_client
                self._supabase_client = create_client(url, key)
            except Exception:
                self._supabase_client = None

        self._inicializar_datos_semilla()

    def _inicializar_datos_semilla(self) -> None:
        semillas = [
            Expediente(
                id_expediente="a101-2026-mdt",
                codigo_expediente="EXP-2026-0348",
                dni_ruc_titular="20609845121",
                razon_social_nombre="Inversiones Gastronómicas El Mantaro S.A.C.",
                giro_comercial="Restaurante",
                tipo_tramite="Nueva licencia",
                direccion_predio="Av. Mariscal Castilla N.° 1420 - El Tambo",
                area_comercial_m2=125.0,
                nombre_archivo_pdf="exp_0348_restaurante.pdf",
                documentos_faltantes=2,
                inconsistencias_detectadas=2,
                documento_critico_faltante=1,
                texto_extraido_resumen="Formulario TUPA sin firma de arquitecto en plano de distribución ni certificado ITSE.",
                confianza_ocr=95.8,
                tiempo_ocr_seg=1.42,
                estado_tramite="OBSERVABLE_PRIORITARIO",
                dias_habiles_transcurridos=2,
                evaluacion_riesgo=EvaluacionRiesgoDomain(
                    algoritmo_empleado="XGBoostClassifier (F1=0.925 | Recall=96.9%)",
                    resultado_observacion=1,
                    probabilidad_riesgo=0.9420,
                    nivel_riesgo="ALTO",
                    importancia_variables={"documento_critico_faltante": 0.46, "documentos_faltantes": 0.29, "inconsistencias_detectadas": 0.16},
                    latencia_inferencia_ms=1.18,
                ),
            ),
            Expediente(
                id_expediente="a102-2026-mdt",
                codigo_expediente="EXP-2026-0349",
                dni_ruc_titular="10458932147",
                razon_social_nombre="Panificadora San Antonio de Huancayo E.I.R.L.",
                giro_comercial="Panaderia",
                tipo_tramite="Modificacion",
                direccion_predio="Jr. Parra del Riego N.° 640 - El Tambo",
                area_comercial_m2=78.5,
                nombre_archivo_pdf="exp_0349_panaderia.pdf",
                documentos_faltantes=1,
                inconsistencias_detectadas=2,
                documento_critico_faltante=0,
                texto_extraido_resumen="Discrepancia menor en metraje cuadrado declarado entre DDJJ (78.5 m2) y croquis (72 m2).",
                confianza_ocr=96.2,
                tiempo_ocr_seg=1.15,
                estado_tramite="OBSERVABLE_PRIORITARIO",
                dias_habiles_transcurridos=3,
                evaluacion_riesgo=EvaluacionRiesgoDomain(
                    algoritmo_empleado="XGBoostClassifier (F1=0.925 | Recall=96.9%)",
                    resultado_observacion=1,
                    probabilidad_riesgo=0.6150,
                    nivel_riesgo="MEDIO",
                    importancia_variables={"documento_critico_faltante": 0.46, "documentos_faltantes": 0.29, "inconsistencias_detectadas": 0.16},
                    latencia_inferencia_ms=0.95,
                ),
            ),
            Expediente(
                id_expediente="a103-2026-mdt",
                codigo_expediente="EXP-2026-0350",
                dni_ruc_titular="10728491023",
                razon_social_nombre="Bodega Multiservicios Los Andes",
                giro_comercial="Bodega",
                tipo_tramite="Renovacion",
                direccion_predio="Jr. Arequipa N.° 890 - El Tambo",
                area_comercial_m2=42.0,
                nombre_archivo_pdf="exp_0350_bodega.pdf",
                documentos_faltantes=0,
                inconsistencias_detectadas=0,
                documento_critico_faltante=0,
                texto_extraido_resumen="Requisitos TUPA completos. DNI, RUC y Declaración Jurada consistentes al 100%.",
                confianza_ocr=98.1,
                tiempo_ocr_seg=0.89,
                estado_tramite="PRE_CONFORME",
                dias_habiles_transcurridos=1,
                evaluacion_riesgo=EvaluacionRiesgoDomain(
                    algoritmo_empleado="XGBoostClassifier (F1=0.925 | Recall=96.9%)",
                    resultado_observacion=0,
                    probabilidad_riesgo=0.0840,
                    nivel_riesgo="BAJO",
                    importancia_variables={"documento_critico_faltante": 0.46, "documentos_faltantes": 0.29, "inconsistencias_detectadas": 0.16},
                    latencia_inferencia_ms=0.82,
                ),
            ),
        ]
        for exp in semillas:
            self._expedientes[exp.codigo_expediente] = exp
        self._persistir_json()

    def _persistir_json(self) -> None:
        try:
            datos = [
                {
                    "id_expediente": e.id_expediente,
                    "codigo_expediente": e.codigo_expediente,
                    "dni_ruc_titular": e.dni_ruc_titular,
                    "razon_social_nombre": e.razon_social_nombre,
                    "giro_comercial": e.giro_comercial,
                    "tipo_tramite": e.tipo_tramite,
                    "direccion_predio": e.direccion_predio,
                    "area_comercial_m2": e.area_comercial_m2,
                    "documentos_faltantes": e.documentos_faltantes,
                    "inconsistencias_detectadas": e.inconsistencias_detectadas,
                    "documento_critico_faltante": e.documento_critico_faltante,
                    "estado_tramite": e.estado_tramite,
                    "probabilidad_riesgo": e.evaluacion_riesgo.probabilidad_riesgo if e.evaluacion_riesgo else 0.0,
                    "nivel_riesgo": e.evaluacion_riesgo.nivel_riesgo if e.evaluacion_riesgo else "BAJO",
                    "fecha_ingreso": e.fecha_ingreso,
                }
                for e in self._expedientes.values()
            ]
            self._storage_file.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def guardar_expediente(self, expediente: Expediente) -> Expediente:
        self._expedientes[expediente.codigo_expediente] = expediente
        self._persistir_json()
        if self._supabase_client and expediente.evaluacion_riesgo:
            try:
                self._supabase_client.table("expedientes").upsert({
                    "id_expediente": expediente.id_expediente,
                    "codigo_expediente": expediente.codigo_expediente,
                    "dni_ruc_titular_cifrado": expediente.dni_ruc_titular,
                    "razon_social_nombre": expediente.razon_social_nombre,
                    "giro_comercial": expediente.giro_comercial,
                    "tipo_tramite": expediente.tipo_tramite,
                    "direccion_predio": expediente.direccion_predio,
                    "area_comercial_m2": expediente.area_comercial_m2,
                    "estado_tramite": expediente.estado_tramite,
                }).execute()
            except Exception:
                pass
        return expediente

    def listar_todos_priorizados(self) -> List[Expediente]:
        return sorted(
            self._expedientes.values(),
            key=lambda e: e.evaluacion_riesgo.probabilidad_riesgo if e.evaluacion_riesgo else 0.0,
            reverse=True,
        )

    def obtener_por_codigo(self, codigo_expediente: str) -> Optional[Expediente]:
        return self._expedientes.get(codigo_expediente.strip().upper())


class InMemoryUsuarioRepository(UsuarioRepositoryPort):
    """Repositorio de funcionarios municipales autorizados (PMV1-1-HU01)."""

    def __init__(self) -> None:
        self._usuarios = {
            "evaluador@eltambo.gob.pe": Usuario(
                id_usuario="usr-001-mdt",
                nombre_completo="Ing. Simon Ronaldo Gonzales Jacinto",
                correo_institucional="evaluador@eltambo.gob.pe",
                password_hash="hash_municipal_2026",
                rol_operativo="EVALUADOR_LICENCIAS",
            ),
            "mesadepartes@eltambo.gob.pe": Usuario(
                id_usuario="usr-002-mdt",
                nombre_completo="Asist. Diego Uriol Ochoa Vilchez",
                correo_institucional="mesadepartes@eltambo.gob.pe",
                password_hash="hash_municipal_2026",
                rol_operativo="MESA_DE_PARTES",
            ),
        }

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        return self._usuarios.get(correo.strip().lower())
