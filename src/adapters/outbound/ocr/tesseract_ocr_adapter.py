import io
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

try:
    import pytesseract
    from PIL import Image
    from pytesseract import Output
except ImportError:  # pragma: no cover - depende del entorno de ejecución
    pytesseract = None
    Image = None
    Output = None

from src.application.dto.expediente_dto import IngresoExpedienteInputDTO, ResultadoOCRDTO
from src.application.ports.output_ports import ExtractorOCRPort


class PyMuPDFTesseractOCRAdapter(ExtractorOCRPort):
    """PATRÓN ADAPTER: extrae texto digital y aplica Tesseract a páginas escaneadas."""

    PALABRAS_CLAVE_TUPA = [
        "ruc",
        "dni",
        "licencia",
        "declaracion",
        "croquis",
        "plano",
        "seguridad",
        "itse",
    ]
    UMBRAL_TEXTO_DIGITAL = 40
    MAX_CARACTERES_TEXTO = 20000
    DPI_OCR = 200

    @staticmethod
    @lru_cache(maxsize=1)
    def _idiomas_tesseract() -> Tuple[str, ...]:
        if pytesseract is None:
            return ()
        try:
            return tuple(pytesseract.get_languages(config=""))
        except Exception:
            return ()

    def _seleccionar_idioma(self) -> Tuple[str, List[str]]:
        idiomas = list(self._idiomas_tesseract())
        advertencias: List[str] = []
        if "spa" in idiomas:
            return "spa", advertencias
        if "eng" in idiomas:
            advertencias.append(
                "El idioma español (spa) no está instalado en Tesseract; se utilizó eng."
            )
            return "eng", advertencias
        alternativos = [idioma for idioma in idiomas if idioma not in {"osd"}]
        if alternativos:
            advertencias.append(
                "Tesseract no tiene instalado el idioma español; "
                f"se utilizó '{alternativos[0]}'."
            )
            return alternativos[0], advertencias
        return "", advertencias

    def _ocr_pagina(self, page: "pymupdf.Page", idioma: str) -> Tuple[str, float]:
        if pytesseract is None or Image is None or Output is None:
            raise ValueError(
                "El documento contiene páginas escaneadas y el motor Tesseract "
                "no está disponible en el servidor."
            )

        pixmap = page.get_pixmap(dpi=self.DPI_OCR, colorspace=pymupdf.csGRAY)
        imagen = Image.open(io.BytesIO(pixmap.tobytes("png")))
        argumentos: Dict[str, Any] = {"output_type": Output.DICT}
        if idioma:
            argumentos["lang"] = idioma

        datos = pytesseract.image_to_data(imagen, **argumentos)
        palabras = [str(texto).strip() for texto in datos.get("text", []) if str(texto).strip()]
        texto = " ".join(palabras).strip()

        confianzas: List[float] = []
        for valor in datos.get("conf", []):
            try:
                confianza = float(valor)
            except (TypeError, ValueError):
                continue
            if confianza >= 0:
                confianzas.append(confianza)
        confianza_promedio = sum(confianzas) / len(confianzas) if confianzas else 0.0
        return texto, confianza_promedio

    def _abrir_documento(self, contenido: bytes) -> "pymupdf.Document":
        try:
            documento = pymupdf.open(stream=contenido, filetype="pdf")
        except Exception as error:
            raise ValueError(
                "El archivo PDF está dañado o no es un documento PDF válido."
            ) from error

        if documento.needs_pass:
            documento.close()
            raise ValueError(
                "El PDF está protegido con contraseña. Retire la protección antes de cargarlo."
            )
        if not documento.is_pdf:
            documento.close()
            raise ValueError("El archivo cargado no es un documento PDF válido.")
        return documento

    def _calcular_indicadores(
        self,
        dto: IngresoExpedienteInputDTO,
        texto_lower: str,
    ) -> Tuple[int, int, int, List[str]]:
        coincidencias = sum(1 for kw in self.PALABRAS_CLAVE_TUPA if kw in texto_lower)

        indicadores_estimados: List[str] = []

        if dto.documentos_faltantes_manual is not None:
            faltantes = int(dto.documentos_faltantes_manual)
        else:
            faltantes = 0 if coincidencias >= 6 else (1 if coincidencias >= 4 else 2)
            indicadores_estimados.append("documentos_faltantes")

        if dto.inconsistencias_manual is not None:
            inconsistencias = int(dto.inconsistencias_manual)
        else:
            inconsistencias = 0 if dto.dni_ruc_titular.lower() in texto_lower else 1
            indicadores_estimados.append("inconsistencias_detectadas")

        if dto.documento_critico_manual is not None:
            critico = int(dto.documento_critico_manual)
        else:
            critico = (
                1
                if (
                    "falta certificado itse" in texto_lower
                    or (faltantes > 0 and "itse" not in texto_lower)
                )
                else 0
            )
            indicadores_estimados.append("documento_critico_faltante")

        return (
            max(0, min(3, faltantes)),
            max(0, min(3, inconsistencias)),
            1 if critico >= 1 else 0,
            indicadores_estimados,
        )

    def extraer_variables(self, dto: IngresoExpedienteInputDTO) -> ResultadoOCRDTO:
        inicio = time.perf_counter()
        bloques: List[str] = []
        confianzas_pagina: List[float] = []
        paginas_digitales = 0
        paginas_ocr = 0
        advertencias: List[str] = []
        idioma_ocr = ""
        tipo_extraccion = "simulada"

        if dto.contenido_pdf_bytes:
            documento = self._abrir_documento(dto.contenido_pdf_bytes)
            try:
                total_paginas = len(documento)
                for pagina in documento:
                    texto_pagina = pagina.get_text("text").strip()
                    if len(texto_pagina) >= self.UMBRAL_TEXTO_DIGITAL:
                        bloques.append(texto_pagina)
                        confianzas_pagina.append(100.0)
                        paginas_digitales += 1
                        continue

                    if not idioma_ocr:
                        idioma_ocr, avisos_idioma = self._seleccionar_idioma()
                        advertencias.extend(avisos_idioma)
                    if not self._idiomas_tesseract():
                        raise ValueError(
                            "El documento contiene páginas escaneadas y Tesseract OCR "
                            "no está instalado o no está disponible en el servidor."
                        )

                    texto_ocr, confianza_ocr = self._ocr_pagina(pagina, idioma_ocr)
                    if texto_ocr:
                        bloques.append(texto_ocr)
                    confianzas_pagina.append(confianza_ocr)
                    paginas_ocr += 1
                    if not texto_ocr:
                        advertencias.append(
                            f"No se reconoció texto en la página {pagina.number + 1}."
                        )
            except ValueError:
                raise
            except Exception as error:
                raise ValueError(
                    "No se pudo procesar el contenido del PDF. Verifique que el "
                    "documento no esté dañado."
                ) from error
            finally:
                documento.close()

            texto_extraido = "\n".join(bloques).strip()
            if paginas_digitales and paginas_ocr:
                tipo_extraccion = "mixta"
            elif paginas_ocr:
                tipo_extraccion = "ocr"
            elif paginas_digitales:
                tipo_extraccion = "digital"

            if not texto_extraido:
                raise ValueError(
                    "No se pudo extraer texto del PDF. Verifique que el documento "
                    "no esté vacío o que las páginas escaneadas sean legibles."
                )
            num_paginas = total_paginas
        else:
            texto_extraido = (
                f"Declaración Jurada TUPA El Tambo - {dto.giro_comercial} - {dto.tipo_tramite}"
            )
            num_paginas = 1
            advertencias.append(
                "No se adjuntó un PDF; los indicadores se estimaron con datos del formulario."
            )

        texto_lower = texto_extraido.lower()
        faltantes, inconsistencias, critico, indicadores_estimados = self._calcular_indicadores(
            dto, texto_lower
        )

        if confianzas_pagina:
            confianza_promedio = sum(confianzas_pagina) / len(confianzas_pagina)
        else:
            confianza_promedio = 0.0

        resumen = texto_extraido[:240].replace("\n", " ").strip()
        if not resumen:
            resumen = f"Fojas procesadas ({num_paginas} págs.) - Giro: {dto.giro_comercial}"

        if dto.documentos_faltantes_manual is None and dto.inconsistencias_manual is None and dto.documento_critico_manual is None:
            modo_indicadores = "automatico"
        elif indicadores_estimados:
            modo_indicadores = "mixto"
        else:
            modo_indicadores = "manual"

        metadatos: Dict[str, Any] = {
            "motor": "PyMuPDF + Tesseract OCR" if paginas_ocr else "PyMuPDF",
            "tipo_extraccion": tipo_extraccion,
            "paginas_totales": num_paginas,
            "paginas_texto_digital": paginas_digitales,
            "paginas_ocr": paginas_ocr,
            "idioma_ocr": idioma_ocr or None,
            "idiomas_tesseract": list(self._idiomas_tesseract()),
            "advertencias": advertencias,
            "modo_indicadores": modo_indicadores,
            "indicadores_estimados": indicadores_estimados,
        }

        tiempo_total = max(0.012, time.perf_counter() - inicio)

        return ResultadoOCRDTO(
            documentos_faltantes=faltantes,
            inconsistencias_detectadas=inconsistencias,
            documento_critico_faltante=critico,
            texto_resumen=resumen,
            confianza_ocr=confianza_promedio,
            tiempo_seg=tiempo_total,
            texto_extraido_completo=texto_extraido[: self.MAX_CARACTERES_TEXTO],
            metadatos_ocr=metadatos,
        )
