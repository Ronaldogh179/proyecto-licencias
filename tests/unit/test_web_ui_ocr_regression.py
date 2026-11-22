from pathlib import Path

HTML = Path("src/adapters/inbound/web_ui/index.html").read_text(encoding="utf-8")


def test_formulario_ocr_expone_estado_progreso_y_modo_automatico():
    assert 'id="btnEvalOcr"' in HTML
    assert 'id="evalFeedback"' in HTML
    assert 'id="modoIndicadores"' in HTML
    assert 'name="modo_indicadores"' in HTML
    assert 'value="automatico"' in HTML
    assert "let evalEnCurso = false;" in HTML
    assert "if (evalEnCurso) return;" in HTML
    assert "button.disabled = true;" in HTML
    assert "button.disabled = false;" in HTML


def test_panel_resultados_inicia_sin_datos_de_ejemplo():
    assert 'id="resultadoMLPlaceholder"' in HTML
    assert 'id="resultadoMLContenido" class="mt-4 space-y-4 hidden"' in HTML
    assert 'id="riesgoProbTxt">--<' in HTML
    assert 'id="ocrResumen">--<' in HTML
    assert 'id="mlLatencia" class="text-emerald-700 font-bold">--<' in HTML
    assert "Sin evaluación ejecutada" in HTML


def test_handler_ocr_maneja_sesion_permisos_conexion_y_restaura_boton():
    assert "res.status === 401" in HTML
    assert "res.status === 403" in HTML
    assert "res.status === 413" in HTML
    assert "res.status === 422" in HTML
    assert "sessionStorage.removeItem(SIMEL_TOKEN_KEY)" in HTML
    assert "No se pudo conectar con el servidor SIMEL" in HTML
    assert "formData.delete('documentos_faltantes')" in HTML
    assert "formData.delete('inconsistencias_detectadas')" in HTML
    assert "formData.delete('documento_critico_faltante')" in HTML
    assert "button.innerText = labelOriginal;" in HTML


def test_resultados_ocr_muestran_archivo_texto_y_confianza_real():
    assert 'id="ocrArchivo"' in HTML
    assert 'id="ocrExpediente"' in HTML
    assert 'id="ocrTextoExtraido"' in HTML
    assert 'id="ocrConfianza"' in HTML
    assert "expediente.texto_extraido_completo" in HTML
    assert "expediente.confianza_ocr" in HTML
    assert "requieren revisión del evaluador" in HTML
