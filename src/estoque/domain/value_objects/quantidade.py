# src/inventory/domain/value_objects/quantidade.py
"""Quantity value object."""

from decimal import Decimal
from typing import Any

from src.estoque.domain.value_objects.unidade_medida import UnidadeMedida
from src.shared.domain.value_objects.base import ValueObject
from src.shared.domain.exceptions.base import ValidationException


class Quantidade(ValueObject):
    """Quantity value object."""
    
    def __init__(self, valor: int | float | Decimal, unidade: UnidadeMedida):
        if isinstance(valor, (int, float)):
            valor = Decimal(str(valor))
        
        if valor < 0:
            raise ValidationException("Quantity cannot be negative")
        
        # Round to 3 decimal places for precision
        self.valor = valor.quantize(Decimal('0.001'))
        self.unidade = unidade
    
    def add(self, other: "Quantidade") -> "Quantidade":
        """Add quantities (must have same unit)."""
        if self.unidade != other.unidade:
            raise ValidationException(
                f"Cannot add different units: {self.unidade} + {other.unidade}"
            )
        
        return Quantidade(self.valor + other.valor, self.unidade)
    
    def subtract(self, other: "Quantidade") -> "Quantidade":
        """Subtract quantities (must have same unit)."""
        if self.unidade != other.unidade:
            raise ValidationException(
                f"Cannot subtract different units: {self.unidade} - {other.unidade}"
            )
        
        new_value = self.valor - other.valor
        if new_value < 0:
            raise ValidationException("Resulting quantity cannot be negative")
        
        return Quantidade(new_value, self.unidade)
    
    def is_greater_than(self, other: "Quantidade") -> bool:
        """Check if this quantity is greater than other."""
        if self.unidade != other.unidade:
            raise ValidationException(
                f"Cannot compare different units: {self.unidade} vs {other.unidade}"
            )
        
        return self.valor > other.valor
    
    def is_less_than(self, other: "Quantidade") -> bool:
        """Check if this quantity is less than other."""
        if self.unidade != other.unidade:
            raise ValidationException(
                f"Cannot compare different units: {self.unidade} vs {other.unidade}"
            )
        
        return self.valor < other.valor
    
    def to_int(self) -> int:
        """Convert to integer (for database storage)."""
        return int(self.valor)
    
    def to_float(self) -> float:
        """Convert to float."""
        return float(self.valor)
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.valor} {self.unidade}"