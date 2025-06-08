# src/inventory/domain/value_objects/sku.py
"""SKU value object."""

import re
from typing import Any

from src.shared.domain.value_objects.base import ValueObject
from src.shared.domain.exceptions.base import ValidationException


class SKU(ValueObject):
    """Product SKU (Stock Keeping Unit) value object."""
    
    # SKU pattern: letters, numbers, hyphens, max 50 chars
    SKU_PATTERN = re.compile(r'^[A-Z0-9\-]{1,50}$')
    
    def __init__(self, codigo: str):
        if not codigo:
            raise ValidationException("SKU cannot be empty")
        
        codigo = codigo.strip().upper()
        
        if not self.SKU_PATTERN.match(codigo):
            raise ValidationException(
                f"Invalid SKU format: {codigo}. Must contain only letters, numbers and hyphens (max 50 chars)"
            )
        
        self.codigo = codigo
    
    def __str__(self) -> str:
        """String representation."""
        return self.codigo