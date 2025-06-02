# src/inventory/domain/services/estoque_service.py
"""Inventory domain service."""

from typing import List, Optional
from uuid import UUID

from src.shared.domain.exceptions.base import BusinessRuleException
from src.produto.domain.entities.produto import Produto
from src.estoque.domain.entities.estoque_produto import EstoqueProduto


class EstoqueService:
    """Domain service for inventory operations."""
    
    @staticmethod
    def validar_movimentacao_estoque(
        estoque: EstoqueProduto,
        produto: Produto,
        quantidade: int,
        tipo_operacao: str
    ) -> None:
        """Validate inventory movement."""
        
        # Check if product is active
        if not produto.ativo:
            raise BusinessRuleException(f"Cannot move stock for inactive product: {produto.sku}")
        
        # Check unit consistency
        if estoque.unidade_medida != produto.unidade_medida:
            raise BusinessRuleException(
                f"Unit mismatch between product and inventory: "
                f"{produto.unidade_medida} vs {estoque.unidade_medida}"
            )
        
        # Validate quantity
        if quantidade <= 0:
            raise BusinessRuleException("Movement quantity must be positive")
        
        # Specific validations by operation type
        if tipo_operacao in ["saida", "remover"]:
            if not estoque.has_available_stock(quantidade):
                raise BusinessRuleException(
                    f"Insufficient stock for {produto.sku}. "
                    f"Available: {estoque.quantidade_disponivel}, Requested: {quantidade}"
                )
    
    @staticmethod
    def calcular_valor_total_estoque(
        estoques: List[EstoqueProduto],
        precos_produtos: dict[UUID, float]
    ) -> float:
        """Calculate total inventory value."""
        total = 0.0
        
        for estoque in estoques:
            preco = precos_produtos.get(estoque.produto_id, 0.0)
            total += estoque.quantidade_atual * preco
        
        return total
    
    @staticmethod
    def identificar_produtos_baixo_estoque(
        estoques: List[EstoqueProduto]
    ) -> List[EstoqueProduto]:
        """Identify products with low stock."""
        return [
            estoque for estoque in estoques
            if estoque.is_below_minimum()
        ]
    
    @staticmethod
    def identificar_produtos_sem_estoque(
        estoques: List[EstoqueProduto]
    ) -> List[EstoqueProduto]:
        """Identify products out of stock."""
        return [
            estoque for estoque in estoques
            if estoque.is_out_of_stock()
        ]
