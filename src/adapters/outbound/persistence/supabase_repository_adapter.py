import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional
import httpx
from dotenv import load_dotenv
from src.application.ports.output_ports import ExpedienteRepositoryPort, UsuarioRepositoryPort
from src.domain.entities.expediente import EvaluacionRiesgoDomain, Expediente
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


class HybridSupabaseExpedienteRepository(ExpedienteRepositoryPort):
    """PATRÓN REPOSITORY: Sincroniza con Supabase PostgreSQL Cloud y mantiene persistencia local."""

    def __init__(self, db_path: str = "src/infrastructure/ml_artifacts/bd_expedientes_local.json") -> None:
        self._db_file = Path(db_path)
        self._db_file.parent.mkdir(parents=True, exist_ok=True)
        self._supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self._supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_KEY", "")
        self._expedientes: List[Expediente] = []
        self._cargar_semilla_o_archivo()

    def _sincronizar_a_supabase_cloud(self, expediente: Expediente) -> None:
        if not self._supabase_url or not self._supabase_key:
            return
        try:
            ev = expediente.evaluacion_riesgo
            payload = {
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
                "probabilidad_riesgo": ev.probabilidad_riesgo if ev else 0.0,
                "nivel_riesgo": ev.nivel_riesgo if ev else "BAJO",
                "estado_tramite": expediente.estado_tramite,
                "dias_habiles_transcurridos": expediente.dias_habiles_transcurridos,
            }
            headers = {
                "apikey": self._supabase_key,
                "Authorization": f"Bearer {self._supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            }
            httpx.post(
                f"{self._supabase_url}/rest/v1/expedientes?on_conflict=codigo_expediente",
                json=payload,
                headers=headers,
                timeout=3.5,
            )
        except Exception:
            pass

    def _cargar_semilla_o_archivo(self) -> None:
        if self._db_file.exists():
            try:
                raw = json.loads(self._db_file.read_text(encoding="utf-8"))
                self._expedientes = []
                for item in raw:
                    ev = item.get("evaluacion_riesgo")
                    ev_obj = EvaluacionRiesgoDomain(**ev) if ev else None
                    item_copy = {k: v for k, v in item.items() if k != "evaluacion_riesgo"}
                    self._expedientes.append(Expediente(**item_copy, evaluacion_riesgo=ev_obj))
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

    def _persistir_en_disco(self) -> None:
        data = [asdict(e) for e in self._expedientes]
        self._db_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def guardar_expediente(self, expediente: Expediente) -> Expediente:
        self._expedientes = [
            e for e in self._expedientes if e.codigo_expediente != expediente.codigo_expediente
        ]
        self._expedientes.append(expediente)
        self._persistir_en_disco()
        self._sincronizar_a_supabase_cloud(expediente)
        return expediente

    def listar_todos_priorizados(self) -> List[Expediente]:
        return sorted(
            self._expedientes,
            key=lambda x: x.evaluacion_riesgo.probabilidad_riesgo if x.evaluacion_riesgo else 0.0,
            reverse=True,
        )

    def obtener_por_codigo(self, codigo_expediente: str) -> Optional[Expediente]:
        for e in self._expedientes:
            if e.codigo_expediente == codigo_expediente.strip().upper():
                return e
        return None
