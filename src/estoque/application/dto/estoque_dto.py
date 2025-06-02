# src/inventory/application/dto/estoque_dto.py
"""Inventory DTOs."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from src.produto.application.dto.produto_dto import ProdutoResponseDTO
from src.shared.application.dto.base import BaseDTO, CreateDTO, UpdateDTO, ResponseDTO


class EstoqueCreateDTO(CreateDTO):
    """DTO for creating inventory records."""
    produto_id: UUID = Field(..., description="Product ID")
    quantidade_atual: int = Field(default=0, ge=0, description="Current quantity")
    quantidade_reservada: int = Field(default=0, ge=0, description="Reserved quantity")
    nivel_minimo: int = Field(default=0, ge=0, description="Minimum level")
    unidade_medida: str = Field(..., description="Unit of measure")


class EstoqueUpdateDTO(UpdateDTO):
    """DTO for updating inventory."""
    quantidade_atual: Optional[int] = Field(None, ge=0)
    quantidade_reservada: Optional[int] = Field(None, ge=0)
    nivel_minimo: Optional[int] = Field(None, ge=0)


class EstoqueMovimentacaoDTO(BaseDTO):
    """DTO for inventory movements."""
    produto_id: UUID = Field(..., description="Product ID")
    quantidade: int = Field(..., gt=0, description="Quantity to move")
    motivo: str = Field(default="", max_length=500, description="Movement reason")


class EstoqueAjusteDTO(BaseDTO):
    """DTO for inventory adjustments."""
    produto_id: UUID = Field(..., description="Product ID")
    nova_quantidade: int = Field(..., ge=0, description="New quantity")
    motivo: str = Field(..., min_length=1, max_length=500, description="Adjustment reason")


class EstoqueReservaDTO(BaseDTO):
    """DTO for stock reservations."""
    produto_id: UUID = Field(..., description="Product ID")
    quantidade: int = Field(..., gt=0, description="Quantity to reserve")


class EstoqueResponseDTO(ResponseDTO):
    """DTO for inventory responses."""
    produto_id: UUID
    quantidade_atual: int
    quantidade_reservada: int
    quantidade_disponivel: int
    nivel_minimo: int
    unidade_medida: str
    atualizado_em: datetime
    is_below_minimum: bool = Field(description="Is below minimum level")
    is_out_of_stock: bool = Field(description="Is out of stock")


class EstoqueComProdutoDTO(BaseDTO):
    """DTO for inventory with product information."""
    estoque: EstoqueResponseDTO
    produto: "ProdutoResponseDTO"


class EstoqueListResponseDTO(BaseDTO):
    """DTO for inventory list responses."""
    estoques: List[EstoqueResponseDTO]
    total: int
    page: int
    page_size: int


class EstoqueBaixoDTO(BaseDTO):
    """DTO for low stock report."""
    produtos_baixo_estoque: List[EstoqueComProdutoDTO]
    total: int


class EstoqueZeradoDTO(BaseDTO):
    """DTO for out of stock report."""
    produtos_sem_estoque: List[EstoqueComProdutoDTO]
    total: int