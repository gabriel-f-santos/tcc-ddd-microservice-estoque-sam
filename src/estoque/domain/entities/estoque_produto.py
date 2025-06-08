# src/inventory/domain/entities/estoque_produto.py
"""Product inventory entity."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from src.estoque.domain.value_objects.unidade_medida import UnidadeMedida
from src.shared.domain.entities.base import AggregateRoot, Entity
from src.shared.domain.exceptions.base import ValidationException, BusinessRuleException
from src.estoque.domain.value_objects.quantidade import Quantidade


class EstoqueProduto(Entity):
    """Product inventory entity."""
    
    def __init__(
        self,
        produto_id: UUID,
        quantidade_atual: int,
        unidade_medida: UnidadeMedida | str,
        quantidade_reservada: int = 0,
        nivel_minimo: int = 0,
        id: UUID | None = None
    ):
        super().__init__(id)
        
        self._produto_id = produto_id
        
        # Validate quantities
        if quantidade_atual < 0:
            raise ValidationException("Current quantity cannot be negative")
        if quantidade_reservada < 0:
            raise ValidationException("Reserved quantity cannot be negative")
        if nivel_minimo < 0:
            raise ValidationException("Minimum level cannot be negative")
        if quantidade_reservada > quantidade_atual:
            raise ValidationException("Reserved quantity cannot exceed current quantity")
        
        self._quantidade_atual = quantidade_atual
        self._quantidade_reservada = quantidade_reservada
        self._nivel_minimo = nivel_minimo
        
        # Unit of measure
        if isinstance(unidade_medida, str):
            unidade_medida = UnidadeMedida(unidade_medida)
        self._unidade_medida = unidade_medida
        
        self._atualizado_em = datetime.utcnow()
    
    @property
    def produto_id(self) -> UUID:
        """Product ID."""
        return self._produto_id
    
    @property
    def quantidade_atual(self) -> int:
        """Current quantity."""
        return self._quantidade_atual
    
    @property
    def quantidade_reservada(self) -> int:
        """Reserved quantity."""
        return self._quantidade_reservada
    
    @property
    def quantidade_disponivel(self) -> int:
        """Available quantity (current - reserved)."""
        return self._quantidade_atual - self._quantidade_reservada
    
    @property
    def nivel_minimo(self) -> int:
        """Minimum level."""
        return self._nivel_minimo
    
    @property
    def unidade_medida(self) -> UnidadeMedida:
        """Unit of measure."""
        return self._unidade_medida
    
    @property
    def atualizado_em(self) -> datetime:
        """Last updated timestamp."""
        return self._atualizado_em
    
    def adicionar_estoque(self, quantidade: int, motivo: str = "") -> None:
        """Add stock."""
        if quantidade <= 0:
            raise ValidationException("Quantity to add must be positive")
        
        self._quantidade_atual += quantidade
        self._atualizado_em = datetime.utcnow()
    
    def remover_estoque(self, quantidade: int, motivo: str = "") -> None:
        """Remove stock."""
        if quantidade <= 0:
            raise ValidationException("Quantity to remove must be positive")
        
        if quantidade > self.quantidade_disponivel:
            raise BusinessRuleException(
                f"Insufficient available stock. Available: {self.quantidade_disponivel}, "
                f"Requested: {quantidade}"
            )
        
        self._quantidade_atual -= quantidade
        self._atualizado_em = datetime.utcnow()

    
    def liberar_reserva(self, quantidade: int) -> None:
        """Release reserved stock."""
        if quantidade <= 0:
            raise ValidationException("Quantity to release must be positive")
        
        if quantidade > self._quantidade_reservada:
            raise BusinessRuleException(
                f"Cannot release more than reserved. Reserved: {self._quantidade_reservada}, "
                f"Requested: {quantidade}"
            )
        
        self._quantidade_reservada -= quantidade
        self._atualizado_em = datetime.utcnow()
    
    def ajustar_estoque(self, nova_quantidade: int, motivo: str = "") -> None:
        """Adjust stock to new quantity."""
        if nova_quantidade < 0:
            raise ValidationException("New quantity cannot be negative")
        
        if nova_quantidade < self._quantidade_reservada:
            raise BusinessRuleException(
                f"New quantity cannot be less than reserved quantity. "
                f"Reserved: {self._quantidade_reservada}, New: {nova_quantidade}"
            )
        
        self._quantidade_atual = nova_quantidade
        self._atualizado_em = datetime.utcnow()
    
    def update_minimum_level(self, nivel_minimo: int) -> None:
        """Update minimum level."""
        if nivel_minimo < 0:
            raise ValidationException("Minimum level cannot be negative")
        
        self._nivel_minimo = nivel_minimo
        self._atualizado_em = datetime.utcnow()
    
    def is_below_minimum(self) -> bool:
        """Check if current stock is below minimum level."""
        return self._quantidade_atual <= self._nivel_minimo
    
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock."""
        return self._quantidade_atual == 0
    
    def has_available_stock(self, quantidade: int) -> bool:
        """Check if has enough available stock."""
        return self.quantidade_disponivel >= quantidade
    
class EstoqueProdutoReplication(AggregateRoot):
    """Product aggregate root."""
    
    def __init__(
        self,
        sku: SKU | str,
        nome: str,
        descricao: str,
        categoria: str,
        unidade_medida: UnidadeMedida | str,
        nivel_minimo: int = 0,
        ativo: bool = True,
        id: UUID | None = None
    ):
        super().__init__(id)
        
        # Validate and set SKU
        if isinstance(sku, str):
            sku = SKU(sku)
        self._sku = sku
        
        # Validate and set name
        if not nome or not nome.strip():
            raise ValidationException("Product name cannot be empty")
        self._nome = nome.strip()
        
        # Set description
        self._descricao = descricao.strip() if descricao else ""
        
        # Validate and set category
        if not categoria or not categoria.strip():
            raise ValidationException("Product category cannot be empty")
        self._categoria = categoria.strip()
        
        # Validate and set unit of measure
        if isinstance(unidade_medida, str):
            unidade_medida = UnidadeMedida(unidade_medida)
        self._unidade_medida = unidade_medida
        
        # Validate and set minimum level
        if nivel_minimo < 0:
            raise ValidationException("Minimum level cannot be negative")
        self._nivel_minimo = nivel_minimo
        
        # Set status
        self._ativo = ativo
    
    @property
    def sku(self) -> SKU:
        """Product SKU."""
        return self._sku
    
    @property
    def nome(self) -> str:
        """Product name."""
        return self._nome
    
    @property
    def descricao(self) -> str:
        """Product description."""
        return self._descricao
    
    @property
    def categoria(self) -> str:
        """Product category."""
        return self._categoria
    
    @property
    def unidade_medida(self) -> UnidadeMedida:
        """Product unit of measure."""
        return self._unidade_medida
    
    @property
    def nivel_minimo(self) -> int:
        """Minimum stock level."""
        return self._nivel_minimo
    
    @property
    def ativo(self) -> bool:
        """Product active status."""
        return self._ativo