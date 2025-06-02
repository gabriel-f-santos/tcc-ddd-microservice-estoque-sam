# src/inventory/infrastructure/repositories/sqlalchemy_estoque_repository.py
"""SQLAlchemy implementation of EstoqueRepository."""

from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.estoque.domain.entities.estoque_produto import EstoqueProduto
from src.estoque.domain.repositories.estoque_repository import EstoqueRepository
from src.produto.domain.value_objects.unidade_medida import UnidadeMedida
from src.estoque.infrastructure.models.estoque_model import EstoqueModel

logger = structlog.get_logger()


class SqlAlchemyEstoqueRepository(EstoqueRepository):
    """SQLAlchemy implementation of EstoqueRepository."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
    
    async def get_by_id(self, id: UUID) -> Optional[EstoqueProduto]:
        """Get inventory by ID."""
        try:
            query = select(EstoqueModel).where(EstoqueModel.id == id)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                return None
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error getting inventory by ID", inventory_id=str(id), error=str(e))
            raise
    
    async def get_by_produto_id(self, produto_id: UUID) -> Optional[EstoqueProduto]:
        """Get inventory by product ID."""
        try:
            query = select(EstoqueModel).where(EstoqueModel.produto_id == produto_id)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                return None
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error getting inventory by product ID", product_id=str(produto_id), error=str(e))
            raise
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[EstoqueProduto]:
        """Get all inventory records with pagination."""
        try:
            query = (
                select(EstoqueModel)
                .offset(skip)
                .limit(limit)
                .order_by(EstoqueModel.atualizado_em.desc())
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error getting all inventory", skip=skip, limit=limit, error=str(e))
            raise
    
    async def get_low_stock_products(self, skip: int = 0, limit: int = 100) -> List[EstoqueProduto]:
        """Get products with low stock."""
        try:
            query = (
                select(EstoqueModel)
                .where(EstoqueModel.quantidade_atual <= EstoqueModel.nivel_minimo)
                .offset(skip)
                .limit(limit)
                .order_by(EstoqueModel.quantidade_atual)
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error getting low stock products", skip=skip, limit=limit, error=str(e))
            raise
    
    async def get_out_of_stock_products(self, skip: int = 0, limit: int = 100) -> List[EstoqueProduto]:
        """Get products out of stock."""
        try:
            query = (
                select(EstoqueModel)
                .where(EstoqueModel.quantidade_atual == 0)
                .offset(skip)
                .limit(limit)
                .order_by(EstoqueModel.atualizado_em.desc())
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error getting out of stock products", skip=skip, limit=limit, error=str(e))
            raise
    
    async def get_products_with_stock(self, skip: int = 0, limit: int = 100) -> List[EstoqueProduto]:
        """Get products with available stock."""
        try:
            query = (
                select(EstoqueModel)
                .where(EstoqueModel.quantidade_atual > EstoqueModel.quantidade_reservada)
                .offset(skip)
                .limit(limit)
                .order_by(EstoqueModel.quantidade_atual.desc())
            )
            result = await self.db.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error("Error getting products with stock", skip=skip, limit=limit, error=str(e))
            raise
    
    async def create(self, entity: EstoqueProduto) -> EstoqueProduto:
        """Create new inventory record."""
        try:
            model = self._entity_to_model(entity)
            self.db.add(model)
            await self.db.flush()
            await self.db.refresh(model)
            
            logger.info("Inventory created", inventory_id=str(model.id), product_id=str(model.produto_id))
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error creating inventory", product_id=str(entity.produto_id), error=str(e))
            await self.db.rollback()
            raise
    
    async def update(self, entity: EstoqueProduto) -> EstoqueProduto:
        """Update existing inventory record."""
        try:
            query = select(EstoqueModel).where(EstoqueModel.id == entity.id)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                raise ValueError(f"Inventory not found: {entity.id}")
            
            # Update fields
            model.quantidade_atual = entity.quantidade_atual
            model.quantidade_reservada = entity.quantidade_reservada
            model.nivel_minimo = entity.nivel_minimo
            model.unidade_medida = entity.unidade_medida.codigo
            model.atualizado_em = entity.atualizado_em
            
            await self.db.flush()
            await self.db.refresh(model)
            
            logger.info("Inventory updated", inventory_id=str(model.id), product_id=str(model.produto_id))
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error("Error updating inventory", inventory_id=str(entity.id), error=str(e))
            await self.db.rollback()
            raise
    
    async def delete(self, id: UUID) -> bool:
        """Delete inventory record by ID."""
        try:
            query = select(EstoqueModel).where(EstoqueModel.id == id)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
            
            if model is None:
                return False
            
            await self.db.delete(model)
            await self.db.flush()
            
            logger.info("Inventory deleted", inventory_id=str(id))
            return True
            
        except Exception as e:
            logger.error("Error deleting inventory", inventory_id=str(id), error=str(e))
            await self.db.rollback()
            raise
    
    async def count(self) -> int:
        """Count total inventory records."""
        try:
            query = select(func.count(EstoqueModel.id))
            result = await self.db.execute(query)
            return result.scalar_one()
            
        except Exception as e:
            logger.error("Error counting inventory", error=str(e))
            raise
    
    def _entity_to_model(self, entity: EstoqueProduto) -> EstoqueModel:
        """Convert entity to SQLAlchemy model."""
        return EstoqueModel(
            id=entity.id,
            produto_id=entity.produto_id,
            quantidade_atual=entity.quantidade_atual,
            quantidade_reservada=entity.quantidade_reservada,
            nivel_minimo=entity.nivel_minimo,
            unidade_medida=entity.unidade_medida.codigo,
            atualizado_em=entity.atualizado_em
        )
    
    def _model_to_entity(self, model: EstoqueModel) -> EstoqueProduto:
        """Convert SQLAlchemy model to entity."""
        entity = EstoqueProduto(
            id=model.id,
            produto_id=model.produto_id,
            quantidade_atual=model.quantidade_atual,
            quantidade_reservada=model.quantidade_reservada,
            nivel_minimo=model.nivel_minimo,
            unidade_medida=UnidadeMedida(model.unidade_medida)
        )
        
        # Set timestamps manually
        entity._atualizado_em = model.atualizado_em
        
        return entity