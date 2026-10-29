import hashlib
import math
import re
import unicodedata
from dataclasses import replace
from typing import Dict, List

from src.application.ports.output_ports import MotorRAGZonificacionPort
from src.domain.entities.normativa_rag import FragmentoNormativoDomain


class PgVectorRAGAdapter(MotorRAGZonificacionPort):
    """Adaptador RAG determinista con corpus normativo pre-indexado y similitud del coseno."""

    DIMENSION = 16
    GIROS = ["Restaurante", "Bodega", "Oficina", "Panaderia", "Tienda"]
    ZONAS = ["CZ", "RDM", "CV", "I1"]
    CIIU = {
        "Restaurante": "5610",
        "Bodega": "4711",
        "Oficina": "6910",
        "Panaderia": "1071",
        "Tienda": "4771",
    }
    AREAS_MAXIMAS = {
        "Restaurante": {"CZ": 150.0, "RDM": 80.0, "CV": 120.0, "I1": 200.0},
        "Bodega": {"CZ": 60.0, "RDM": 50.0, "CV": 80.0, "I1": 100.0},
        "Oficina": {"CZ": 100.0, "RDM": 120.0, "CV": 150.0, "I1": 200.0},
        "Panaderia": {"CZ": 70.0, "RDM": 80.0, "CV": 90.0, "I1": 120.0},
        "Tienda": {"CZ": 50.0, "RDM": 60.0, "CV": 80.0, "I1": 100.0},
    }
    PESO_GIRO = 3.0
    PESO_ZONA = 2.5
    PESO_TEXTO = 0.15

    def __init__(self) -> None:
        self._corpus: List[FragmentoNormativoDomain] = self._construir_corpus_oficial()
        self._vectores: Dict[str, List[float]] = {
            fragmento.id_fragmento: self._construir_vector(
                fragmento.giro_comercial,
                fragmento.zona_urbana,
                fragmento.texto_fragmento_chunk,
            )
            for fragmento in self._corpus
        }

    @staticmethod
    def _normalizar_texto(texto: str) -> str:
        normalizado = unicodedata.normalize("NFKD", (texto or "").strip().lower())
        normalizado = "".join(c for c in normalizado if not unicodedata.combining(c))
        normalizado = re.sub(r"[^a-z0-9\s]", " ", normalizado)
        return re.sub(r"\s+", " ", normalizado).strip()

    def _construir_vector(self, giro: str, zona: str, texto: str) -> List[float]:
        vector = [0.0] * self.DIMENSION
        giro_normalizado = self._normalizar_texto(giro)
        zona_normalizada = self._normalizar_texto(zona)

        for indice, giro_oficial in enumerate(self.GIROS):
            if giro_normalizado == self._normalizar_texto(giro_oficial):
                vector[indice] = self.PESO_GIRO
                break

        for indice, zona_oficial in enumerate(self.ZONAS):
            if zona_normalizada == self._normalizar_texto(zona_oficial):
                vector[5 + indice] = self.PESO_ZONA
                break

        bloque_texto = [0.0] * 7
        for token in re.findall(r"[a-z0-9]+", self._normalizar_texto(texto)):
            if len(token) < 3:
                continue
            digest = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            bloque_texto[digest % 7] += 1.0

        norma_texto = math.sqrt(sum(valor * valor for valor in bloque_texto))
        if norma_texto > 0:
            for indice, valor in enumerate(bloque_texto):
                vector[9 + indice] = self.PESO_TEXTO * (valor / norma_texto)

        return vector

    @staticmethod
    def _similitud_coseno(vector_a: List[float], vector_b: List[float]) -> float:
        producto_punto = sum(a * b for a, b in zip(vector_a, vector_b))
        norma_a = math.sqrt(sum(a * a for a in vector_a))
        norma_b = math.sqrt(sum(b * b for b in vector_b))
        if norma_a == 0.0 or norma_b == 0.0:
            return 0.0
        return producto_punto / (norma_a * norma_b)

    @staticmethod
    def _normalizar_vector(vector: List[float]) -> List[float]:
        norma = math.sqrt(sum(valor * valor for valor in vector))
        if norma == 0.0:
            return vector
        return [round(valor / norma, 8) for valor in vector]

    def _construir_corpus_oficial(self) -> List[FragmentoNormativoDomain]:
        corpus: List[FragmentoNormativoDomain] = []
        for giro in self.GIROS:
            codigo_ciiu = self.CIIU[giro]
            for zona in self.ZONAS:
                area_maxima = self.AREAS_MAXIMAS[giro][zona]
                if zona in ("RDM", "I1") and giro in ("Restaurante", "Panaderia"):
                    compatibilidad = "COMPATIBLE_CON_RESTRICCION"
                else:
                    compatibilidad = "COMPATIBLE"

                texto = (
                    "Ordenanza Municipal N.° 018-2024-MDT/CM. Cuadro de Índice de Usos "
                    "para la Ubicación de Actividades Urbanas. Artículo 12.º, inciso c). "
                    f"Clasificación CIIU-{codigo_ciiu} para el giro {giro}. Zona urbana "
                    f"{zona}. Compatibilidad de zonificación: {compatibilidad}. Área máxima "
                    f"permitida: {area_maxima:.2f} m². Ley N.° 28976, Artículo 7.º: la "
                    "licencia de funcionamiento se otorga previa verificación de la "
                    "compatibilidad de la actividad con la zonificación vigente y el área "
                    "declarada en la Declaración Jurada TUPA y en el plano técnico."
                )
                corpus.append(
                    FragmentoNormativoDomain(
                        id_fragmento=f"FRAG-CIIU-{codigo_ciiu}-{zona}",
                        norma_origen="Ordenanza Municipal N.° 018-2024-MDT/CM",
                        articulo_inciso=(
                            f"Artículo 12.º, inciso c) - Cuadro de Índice de Usos "
                            f"CIIU-{codigo_ciiu}"
                        ),
                        codigo_ciiu=codigo_ciiu,
                        giro_comercial=giro,
                        zona_urbana=zona,
                        compatibilidad=compatibilidad,
                        area_maxima_m2=area_maxima,
                        texto_fragmento_chunk=texto,
                        tokens_chunk=500,
                        overlap_tokens=50,
                        similitud_coseno=0.0,
                    )
                )
        return corpus

    def fragmentar_y_vectorizar_norma(self, texto: str, giro: str, zona: str) -> List[float]:
        if not texto or not texto.strip():
            raise ValueError("El texto normativo a vectorizar no puede estar vacío.")
        vector = self._construir_vector(giro, zona, texto)
        return self._normalizar_vector(vector)

    def buscar_similitud_coseno(
        self,
        giro_comercial: str,
        zona_urbana: str,
        area_m2: float,
    ) -> FragmentoNormativoDomain:
        texto_consulta = (
            f"{giro_comercial} {zona_urbana} licencia funcionamiento compatible "
            "ordenanza municipal zonificación área declarada"
        )
        vector_consulta = self._construir_vector(giro_comercial, zona_urbana, texto_consulta)

        giro_normalizado = self._normalizar_texto(giro_comercial)
        zona_normalizada = self._normalizar_texto(zona_urbana)
        candidatos = [
            fragmento
            for fragmento in self._corpus
            if self._normalizar_texto(fragmento.giro_comercial) == giro_normalizado
            and self._normalizar_texto(fragmento.zona_urbana) == zona_normalizada
        ]
        if not candidatos:
            candidatos = list(self._corpus)

        mejor_fragmento = candidatos[0]
        mejor_similitud = -1.0
        for fragmento in candidatos:
            vector_fragmento = self._vectores.get(fragmento.id_fragmento)
            if vector_fragmento is None:
                vector_fragmento = self._construir_vector(
                    fragmento.giro_comercial,
                    fragmento.zona_urbana,
                    fragmento.texto_fragmento_chunk,
                )
                self._vectores[fragmento.id_fragmento] = vector_fragmento
            similitud = self._similitud_coseno(vector_consulta, vector_fragmento)
            if similitud > mejor_similitud:
                mejor_similitud = similitud
                mejor_fragmento = fragmento

        return replace(
            mejor_fragmento,
            similitud_coseno=round(float(mejor_similitud), 4),
        )

    def indexar_fragmento(self, fragmento: FragmentoNormativoDomain) -> None:
        self._corpus = [
            existente
            for existente in self._corpus
            if existente.id_fragmento != fragmento.id_fragmento
        ]
        self._corpus.append(fragmento)
        self._vectores[fragmento.id_fragmento] = self._construir_vector(
            fragmento.giro_comercial,
            fragmento.zona_urbana,
            fragmento.texto_fragmento_chunk,
        )

    def listar_corpus(self) -> List[FragmentoNormativoDomain]:
        return list(self._corpus)
