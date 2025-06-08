# src/inventory/application/services/estoque_application_service.py
"""Inventory application service."""

from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.application.services.base import BaseApplicationService
from src.shared.domain.exceptions.base import ValidationException, BusinessRuleException
from src.estoque.domain.entities.estoque_produto import EstoqueProduto, EstoqueProdutoReplication
from src.estoque.domain.services.estoque_service import EstoqueService
from src.estoque.domain.value_objects.unidade_medida import UnidadeMedida
from src.estoque.infrastructure.repositories.sqlalchemy_estoque_repository import SqlAlchemyEstoqueRepository
from src.estoque.application.dto.estoque_dto import (
    EstoqueCreateDTO,
    EstoqueProdutoResponseDTO,
    EstoqueUpdateDTO,
    EstoqueMovimentacaoDTO,
    EstoqueAjusteDTO,
    EstoqueReservaDTO,
    EstoqueResponseDTO,
    EstoqueComProdutoDTO,
    EstoqueListResponseDTO,
    EstoqueBaixoDTO,
    EstoqueZeradoDTO
)
from src.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class EstoqueApplicationService(BaseApplicationService[EstoqueProduto]):
    """Inventory application service."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.estoque_repository = SqlAlchemyEstoqueRepository(db)
    
    async def create_inventory(self, create_dto: EstoqueCreateDTO) -> EstoqueResponseDTO:
        """Create new inventory record."""
        try:
            # Check if product exists via API
            import httpx
            headers = {"Authorization": f"Bearer {settings.internal_api_key}"}

            async with httpx.AsyncClient(headers=headers) as client:
                try:
                    response = await client.get(f"https://543jlwvv4a.execute-api.us-east-1.amazonaws.com/Prod/api/v1/produtos/{create_dto.produto_id}")
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    product_data = response.json()

                    product = EstoqueProdutoReplication(
                        id=product_data["id"],
                        sku=product_data["sku"],
                        nome=product_data["nome"],
                        descricao=product_data["descricao"],
                        categoria=product_data["categoria"],
                        unidade_medida=product_data["unidade_medida"],
                        nivel_minimo=product_data["nivel_minimo"],
                        ativo=product_data["ativo"]
                    )
                except httpx.HTTPStatusError as e:
                    raise BusinessRuleException(f"Product not found: {create_dto.produto_id} - API error: {e}")
                except httpx.RequestError as e:
                    raise BusinessRuleException(f"Failed to connect to product service: {e}")
            # Check if inventory already exists for this product
            existing = await self.estoque_repository.get_by_produto_id(create_dto.produto_id)
            if existing is not None:
                raise BusinessRuleException(f"Inventory already exists for product: {create_dto.produto_id}")
            
            # Create inventory entity
            inventory = EstoqueProduto(
                produto_id=create_dto.produto_id,
                quantidade_atual=create_dto.quantidade_atual,
                quantidade_reservada=create_dto.quantidade_reservada,
                nivel_minimo=create_dto.nivel_minimo,
                unidade_medida=UnidadeMedida(create_dto.unidade_medida)
            )
            
            # Validate with domain service
            EstoqueService.validar_movimentacao_estoque(
                inventory, product, create_dto.quantidade_atual, "entrada"
            )
            
            # Save to repository
            inventory = await self.estoque_repository.create(inventory)
            await self.db.commit()
            
            logger.info("Inventory created", inventory_id=str(inventory.id), product_id=str(create_dto.produto_id))
            
            return self._entity_to_response_dto(inventory)
            
        except Exception as e:
            logger.error("Inventory creation failed", product_id=str(create_dto.produto_id), error=str(e))
            await self.db.rollback()
            raise
    
    async def get_inventory_by_product_id(self, produto_id: UUID) -> Optional[EstoqueResponseDTO]:
        """Get inventory by product ID."""
        try:
            inventory = await self.estoque_repository.get_by_produto_id(produto_id)
            
            if inventory is None:
                return None
            
            return self._entity_to_response_dto(inventory)
            
        except Exception as e:
            logger.error("Error getting inventory", product_id=str(produto_id), error=str(e))
            raise
    
    async def get_all_inventory(self, skip: int = 0, limit: int = 100) -> EstoqueListResponseDTO:
        """Get all inventory with pagination."""
        try:
            inventories = await self.estoque_repository.get_all(skip, limit)
            total = await self.estoque_repository.count()
            
            inventory_dtos = [self._entity_to_response_dto(inventory) for inventory in inventories]
            
            return EstoqueListResponseDTO(
                estoques=inventory_dtos,
                total=total,
                page=skip // limit + 1 if limit > 0 else 1,
                page_size=limit
            )
            
        except Exception as e:
            logger.error("Error getting all inventory", skip=skip, limit=limit, error=str(e))
            raise
    
    async def add_stock(self, movimento_dto: EstoqueMovimentacaoDTO) -> EstoqueResponseDTO:
        """Add stock to product."""
        try:
            # Get inventory and product
            inventory = await self.estoque_repository.get_by_produto_id(movimento_dto.produto_id)
            if inventory is None:
                raise BusinessRuleException(f"Inventory not found for product: {movimento_dto.produto_id}")
            import httpx
            headers = {"Authorization": f"Bearer {settings.internal_api_key}"}

            async with httpx.AsyncClient(headers=headers) as client:
                try:
                    response = await client.get(f"https://543jlwvv4a.execute-api.us-east-1.amazonaws.com/Prod/api/v1/produtos/{movimento_dto.produto_id}")
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    product_data = response.json()

                    product = EstoqueProdutoReplication(
                        id=product_data["id"],
                        sku=product_data["sku"],
                        nome=product_data["nome"],
                        descricao=product_data["descricao"],
                        categoria=product_data["categoria"],
                        unidade_medida=product_data["unidade_medida"],
                        nivel_minimo=product_data["nivel_minimo"],
                        ativo=product_data["ativo"]
                    )
                except httpx.HTTPStatusError as e:
                    raise BusinessRuleException(f"Product not found: {movimento_dto.produto_id} - API error: {e}")
                except httpx.RequestError as e:
                    raise BusinessRuleException(f"Failed to connect to product service: {e}")
            # Validate movement
            EstoqueService.validar_movimentacao_estoque(
                inventory, product, movimento_dto.quantidade, "entrada"
            )
            
            # Add stock
            inventory.adicionar_estoque(movimento_dto.quantidade, movimento_dto.motivo)
            
            # Save changes
            inventory = await self.estoque_repository.update(inventory)
            await self.db.commit()
            
            logger.info(
                "Stock added",
                product_id=str(movimento_dto.produto_id),
                quantity=movimento_dto.quantidade,
                new_total=inventory.quantidade_atual
            )
            
            return self._entity_to_response_dto(inventory)
            
        except Exception as e:
            logger.error("Add stock failed", product_id=str(movimento_dto.produto_id), error=str(e))
            await self.db.rollback()
            raise
    
    async def remove_stock(self, movimento_dto: EstoqueMovimentacaoDTO) -> EstoqueResponseDTO:
        """Remove stock from product."""
        try:
            # Get inventory and product
            inventory = await self.estoque_repository.get_by_produto_id(movimento_dto.produto_id)
            if inventory is None:
                raise BusinessRuleException(f"Inventory not found for product: {movimento_dto.produto_id}")
            import httpx
            headers = {"Authorization": f"Bearer {settings.internal_api_key}"}

            async with httpx.AsyncClient(headers=headers) as client:
                try:
                    response = await client.get(f"https://543jlwvv4a.execute-api.us-east-1.amazonaws.com/Prod/api/v1/produtos/{movimento_dto.produto_id}")
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    product_data = response.json()

                    product = EstoqueProdutoReplication(
                        id=product_data["id"],
                        sku=product_data["sku"],
                        nome=product_data["nome"],
                        descricao=product_data["descricao"],
                        categoria=product_data["categoria"],
                        unidade_medida=product_data["unidade_medida"],
                        nivel_minimo=product_data["nivel_minimo"],
                        ativo=product_data["ativo"]
                    )
                except httpx.HTTPStatusError as e:
                    raise BusinessRuleException(f"Product not found: {movimento_dto.produto_id} - API error: {e}")
                except httpx.RequestError as e:
                    raise BusinessRuleException(f"Failed to connect to product service: {e}")
            # Validate movement
            EstoqueService.validar_movimentacao_estoque(
                inventory, product, movimento_dto.quantidade, "saida"
            )
            
            # Remove stock
            inventory.remover_estoque(movimento_dto.quantidade, movimento_dto.motivo)
            
            # Save changes
            inventory = await self.estoque_repository.update(inventory)
            await self.db.commit()
            
            logger.info(
                "Stock removed",
                product_id=str(movimento_dto.produto_id),
                quantity=movimento_dto.quantidade,
                new_total=inventory.quantidade_atual
            )
            
            return self._entity_to_response_dto(inventory)
            
        except Exception as e:
            logger.error("Remove stock failed", product_id=str(movimento_dto.produto_id), error=str(e))
            await self.db.rollback()
            raise
    
    async def adjust_stock(self, ajuste_dto: EstoqueAjusteDTO) -> EstoqueResponseDTO:
        """Adjust stock to new quantity."""
        try:
            # Get inventory and product
            inventory = await self.estoque_repository.get_by_produto_id(ajuste_dto.produto_id)
            if inventory is None:
                raise BusinessRuleException(f"Inventory not found for product: {ajuste_dto.produto_id}")
            
            import httpx
            headers = {"Authorization": f"Bearer {settings.internal_api_key}"}

            async with httpx.AsyncClient(headers=headers) as client:
                try:
                    response = await client.get(f"https://543jlwvv4a.execute-api.us-east-1.amazonaws.com/Prod/api/v1/produtos/{ajuste_dto.produto_id}")
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    product_data = response.json()

                    product = EstoqueProdutoReplication(
                        id=product_data["id"],
                        sku=product_data["sku"],
                        nome=product_data["nome"],
                        descricao=product_data["descricao"],
                        categoria=product_data["categoria"],
                        unidade_medida=product_data["unidade_medida"],
                        nivel_minimo=product_data["nivel_minimo"],
                        ativo=product_data["ativo"]
                    )
                except httpx.HTTPStatusError as e:
                    raise BusinessRuleException(f"Product not found: {ajuste_dto.produto_id} - API error: {e}")
                except httpx.RequestError as e:
                    raise BusinessRuleException(f"Failed to connect to product service: {e}")
            # Adjust stock
            old_quantity = inventory.quantidade_atual
            inventory.ajustar_estoque(ajuste_dto.nova_quantidade, ajuste_dto.motivo)
            
            # Save changes
            inventory = await self.estoque_repository.update(inventory)
            await self.db.commit()
            
            logger.info(
                "Stock adjusted",
                product_id=str(ajuste_dto.produto_id),
                old_quantity=old_quantity,
                new_quantity=ajuste_dto.nova_quantidade,
                reason=ajuste_dto.motivo
            )
            
            return self._entity_to_response_dto(inventory)
            
        except Exception as e:
            logger.error("Adjust stock failed", product_id=str(ajuste_dto.produto_id), error=str(e))
            await self.db.rollback()
            raise
    
    async def get_low_stock_report(self) -> EstoqueBaixoDTO:
        """Get low stock report."""
        try:
            low_stock_inventories = await self.estoque_repository.get_low_stock_products()
            
            # Get product details
            produtos_baixo_estoque = []
            for inventory in low_stock_inventories:
                import httpx
                headers = {"Authorization": f"Bearer {settings.internal_api_key}"}
                async with httpx.AsyncClient(headers=headers) as client:
                    try:
                        response = await client.get(f"https://543jlwvv4a.execute-api.us-east-1.amazonaws.com/Prod/api/v1/produtos/{inventory.produto_id}")
                        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                        product_data = response.json()

                        product = EstoqueProdutoReplication(
                            id=product_data["id"],
                            sku=product_data["sku"],
                            nome=product_data["nome"],
                            descricao=product_data["descricao"],
                            categoria=product_data["categoria"],
                            unidade_medida=product_data["unidade_medida"],
                            nivel_minimo=product_data["nivel_minimo"],
                            ativo=product_data["ativo"]
                        )
                        produtos_baixo_estoque.append(EstoqueComProdutoDTO(
                            estoque=self._entity_to_response_dto(inventory),
                            produto=self._product_entity_to_dto(product)
                        ))
                    except httpx.HTTPStatusError as e:
                        logger.error(f"Product not found: {inventory.produto_id} - API error: {e}")
                    except httpx.RequestError as e:
                        logger.error(f"Failed to connect to product service: {e}")
            
            return EstoqueBaixoDTO(
                produtos_baixo_estoque=produtos_baixo_estoque,
                total=len(produtos_baixo_estoque)
            )
            
        except Exception as e:
            logger.error("Error getting low stock report", error=str(e))
            raise
    
    async def get_out_of_stock_report(self) -> EstoqueZeradoDTO:
        """Get out of stock report."""
        try:
            out_of_stock_inventories = await self.estoque_repository.get_out_of_stock_products()
            
            # Get product details
            produtos_sem_estoque = []
            for inventory in out_of_stock_inventories:
                import httpx
                headers = {"Authorization": f"Bearer {settings.internal_api_key}"}
                async with httpx.AsyncClient(headers=headers) as client:
                    try:
                        response = await client.get(f"https://543jlwvv4a.execute-api.us-east-1.amazonaws.com/Prod/api/v1/produtos/{inventory.produto_id}")
                        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                        product_data = response.json()

                        product = EstoqueProdutoReplication(
                            id=product_data["id"],
                            sku=product_data["sku"],
                            nome=product_data["nome"],
                            descricao=product_data["descricao"],
                            categoria=product_data["categoria"],
                            unidade_medida=product_data["unidade_medida"],
                            nivel_minimo=product_data["nivel_minimo"],
                            ativo=product_data["ativo"]
                        )
                        produtos_sem_estoque.append(EstoqueComProdutoDTO(
                            estoque=self._entity_to_response_dto(inventory),
                            produto=self._product_entity_to_dto(product)
                        ))
                    except httpx.HTTPStatusError as e:
                        logger.error(f"Product not found: {inventory.produto_id} - API error: {e}")
                    except httpx.RequestError as e:
                        logger.error(f"Failed to connect to product service: {e}")
            
            return EstoqueZeradoDTO(
                produtos_sem_estoque=produtos_sem_estoque,
                total=len(produtos_sem_estoque)
            )
            
        except Exception as e:
            logger.error("Error getting out of stock report", error=str(e))
            raise
    
    def _entity_to_response_dto(self, inventory: EstoqueProduto) -> EstoqueResponseDTO:
        """Convert entity to response DTO."""
        return EstoqueResponseDTO(
            id=inventory.id,
            produto_id=inventory.produto_id,
            quantidade_atual=inventory.quantidade_atual,
            quantidade_reservada=inventory.quantidade_reservada,
            quantidade_disponivel=inventory.quantidade_disponivel,
            nivel_minimo=inventory.nivel_minimo,
            unidade_medida=inventory.unidade_medida.codigo,
            atualizado_em=inventory.atualizado_em,
            is_below_minimum=inventory.is_below_minimum(),
            is_out_of_stock=inventory.is_out_of_stock(),
            created_at=inventory.atualizado_em,  # Using atualizado_em as created_at
            updated_at=inventory.atualizado_em
        )
    
    def _product_entity_to_dto(self, product: EstoqueProdutoReplication) -> EstoqueProdutoResponseDTO:
        """Convert product entity to DTO."""
        return EstoqueProdutoResponseDTO(
            id=product.id,
            sku=product.sku.codigo,
            nome=product.nome,
            descricao=product.descricao,
            categoria=product.categoria,
            unidade_medida=product.unidade_medida.codigo,
            nivel_minimo=product.nivel_minimo,
            ativo=product.ativo,
            created_at=product.created_at,
            updated_at=product.updated_at
        )