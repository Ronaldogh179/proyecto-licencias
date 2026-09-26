from src.domain.entities.expediente import Expediente

class CalculadorSLAService:
    """Servicio puro de dominio para verificar plazos legales de la Ley N.° 28976."""
    PLAZO_MAXIMO_DIAS_HABILES = 8

    @classmethod
    def calcular_dias_restantes(cls, expediente: Expediente) -> int:
        restantes = cls.PLAZO_MAXIMO_DIAS_HABILES - expediente.dias_habiles_transcurridos
        return max(0, restantes)

    @classmethod
    def estado_semaforo_sla(cls, expediente: Expediente) -> str:
        if not expediente.cumple_sla_legal():
            return "VENCIDO_FUERA_DE_PLAZO"
        if expediente.dias_habiles_transcurridos >= 6:
            return "ALERTA_PROXIMO_A_VENCER"
        return "DENTRO_DEL_PLAZO_LEGAL"
