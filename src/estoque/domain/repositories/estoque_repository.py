# src/inventory/domain/repositories/estoque_repository.py
"""Inventory repository interface."""

from abc import abstractmethod
from typing import Optional, List
from uuid import UUID

from src.shared.infrastructure.repositories.base import BaseRepository
from src.estoque.domain.entities.estoque_produto import EstoqueProduto


class EstoqueRepository(BaseRepository[EstoqueProduto]):
    """Inventory repository interface."""
    
    @abstractmethod
    async def get_by_produto_id(self, produto_id: UUID) -> Optional[EstoqueProduto]:
        """Get inventory by product ID."""
        pass
    
    @abstractmethod
    async def get_low_stock_products(self, skip: int = 0, limit: int = 100) -> List[EstoqueProduto]:
        """Get products with low stock."""
        pass
    
    @abstractmethod
    async def get_out_of_stock_products(self, skip: int = 0, limit: int = 100) -> List[EstoqueProduto]:
        """Get products out of stock."""
        pass
    
    @abstractmethod
    async def get_products_with_stock(self, skip: int = 0, limit: int = 100) -> List[EstoqueProduto]:
        """Get products with available stock."""
        pass