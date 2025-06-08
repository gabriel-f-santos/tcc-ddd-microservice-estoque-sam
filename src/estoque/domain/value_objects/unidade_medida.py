from enum import Enum
from src.shared.domain.exceptions.base import ValidationException
from src.shared.domain.value_objects.base import ValueObject


class TipoUnidadeMedida(str, Enum):
    """Types of units of measure."""
    UNIDADE = "UN"
    QUILOGRAMA = "KG"
    GRAMA = "G"
    LITRO = "L"
    MILILITRO = "ML"
    METRO = "M"
    CENTIMETRO = "CM"
    METRO_QUADRADO = "M2"
    METRO_CUBICO = "M3"
    CAIXA = "CX"
    PACOTE = "PCT"
    FARDO = "FD"


class UnidadeMedida(ValueObject):
    """Unit of measure value object."""
    
    def __init__(self, tipo: TipoUnidadeMedida | str):
        if isinstance(tipo, str):
            try:
                tipo = TipoUnidadeMedida(tipo.upper())
            except ValueError:
                raise ValidationException(f"Invalid unit type: {tipo}")
        
        self.tipo = tipo
    
    @property
    def codigo(self) -> str:
        """Unit code."""
        return self.tipo.value
    
    @property
    def nome(self) -> str:
        """Unit name."""
        names = {
            TipoUnidadeMedida.UNIDADE: "Unidade",
            TipoUnidadeMedida.QUILOGRAMA: "Quilograma",
            TipoUnidadeMedida.GRAMA: "Grama",
            TipoUnidadeMedida.LITRO: "Litro",
            TipoUnidadeMedida.MILILITRO: "Mililitro",
            TipoUnidadeMedida.METRO: "Metro",
            TipoUnidadeMedida.CENTIMETRO: "Centímetro",
            TipoUnidadeMedida.METRO_QUADRADO: "Metro Quadrado",
            TipoUnidadeMedida.METRO_CUBICO: "Metro Cúbico",
            TipoUnidadeMedida.CAIXA: "Caixa",
            TipoUnidadeMedida.PACOTE: "Pacote",
            TipoUnidadeMedida.FARDO: "Fardo",
        }
        return names.get(self.tipo, self.tipo.value)
    
    def __str__(self) -> str:
        """String representation."""
        return self.codigo