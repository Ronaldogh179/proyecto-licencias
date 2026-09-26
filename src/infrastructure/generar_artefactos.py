import json
from pathlib import Path
import pymupdf
from src.infrastructure.container import container

def generar_artefactos_y_pdfs():
    artifacts_dir = Path("src/infrastructure/ml_artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Guardar modelo XGBoost físico y métricas de la PoC
    entrenador = container.entrenador_ml
    entrenador.modelo_xgb.save_model(str(artifacts_dir / "xgboost_licencias_pmv1.json"))
    (artifacts_dir / "metricas_poc_oficiales.json").write_text(
        json.dumps(entrenador.metricas_poc, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Crear 2 PDFs reales del TUPA de la Municipalidad Distrital de El Tambo para pruebas de ingesta OCR
    pdf_dir = Path("muestras_pdf_tupa")
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # PDF 1: Expediente con Riesgo Alto (Falta ITSE y discrepancia de área)
    doc1 = pymupdf.open()
    page1 = doc1.new_page()
    texto1 = (
        "MUNICIPALIDAD DISTRITAL DE EL TAMBO - HUANCAYO\n"
        "FORMATO DE DECLARACION JURADA PARA LICENCIA DE FUNCIONAMIENTO (LEY N. 28976)\n\n"
        "Codigo de Expediente: EXP-2026-0351\n"
        "RUC del Administrado: 20601122334\n"
        "Razon Social: Restaurante Turistico El Huaytapallana S.A.C.\n"
        "Giro Comercial: Restaurante | Tipo de Tramite: Nueva licencia\n"
        "Area declarada en formulario: 110.50 m2 vs Croquis: 82.00 m2 (Inconsistencia)\n"
        "OBSERVACION DE RECEPCION: FALTA CERTIFICADO ITSE Y PLANO ELECTRICO FIRMADO."
    )
    page1.insert_text((50, 70), texto1, fontsize=11)
    doc1.save(str(pdf_dir / "EXP-2026-0351_OBSERVADO.pdf"))
    doc1.close()

    # PDF 2: Expediente Conforme de Riesgo Bajo
    doc2 = pymupdf.open()
    page2 = doc2.new_page()
    texto2 = (
        "MUNICIPALIDAD DISTRITAL DE EL TAMBO - HUANCAYO\n"
        "FORMATO DE DECLARACION JURADA PARA LICENCIA DE FUNCIONAMIENTO (LEY N. 28976)\n\n"
        "Codigo de Expediente: EXP-2026-0352\n"
        "DNI / RUC: 10445566778\n"
        "Titular: Bodega Multiservicios Santa Rosa\n"
        "Requisitos verificados: RUC, DNI, Licencia, Declaracion Jurada, Croquis, Plano, Seguridad ITSE.\n"
        "Todos los documentos obligatorios estan completos y firmados sin inconsistencias."
    )
    page2.insert_text((50, 70), texto2, fontsize=11)
    doc2.save(str(pdf_dir / "EXP-2026-0352_CONFORME.pdf"))
    doc2.close()

if __name__ == "__main__":
    generar_artefactos_y_pdfs()
