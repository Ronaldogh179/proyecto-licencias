from src.domain.entities.expediente import Expediente

class CalculadorSLAService:
    """Servicio puro de dominio para verificar plazos legales de la Ley N.° 28976."""

    PLAZO_MAXIMO_DIAS_HABILES = 8

    @classmethod
    def calcular_dias_restantes(cls, expediente: Expediente) -> int:
        restantes = cls.PLAZO_MAXIMO_DIAS_HABILES - expediente.dias_habiles_transcurridos
        return max(0, restantes)

    @classmethod
    def calcular_dias_restantes_por_dias(cls, dias_habiles_transcurridos: int) -> int:
        restantes = cls.PLAZO_MAXIMO_DIAS_HABILES - int(dias_habiles_transcurridos)
        return max(0, restantes)

    @classmethod
    def cumple_sla(cls, dias_habiles_transcurridos: int) -> bool:
        return int(dias_habiles_transcurridos) <= cls.PLAZO_MAXIMO_DIAS_HABILES

    @classmethod
    def obtener_estado_semaforo(cls, dias_habiles_transcurridos: int) -> str:
        dias = int(dias_habiles_transcurridos)
        if not cls.cumple_sla(dias):
            return "VENCIDO_FUERA_DE_PLAZO"
        if dias >= 6:
            return "ALERTA_PROXIMO_A_VENCER"
        return "DENTRO_DEL_PLAZO_LEGAL"

    @classmethod
    def estado_semaforo_sla(cls, expediente: Expediente) -> str:
        return cls.obtener_estado_semaforo(expediente.dias_habiles_transcurridos)
