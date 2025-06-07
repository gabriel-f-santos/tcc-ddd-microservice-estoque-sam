# src/handlers/estoque_handler.py
"""Estoque (Inventory) Lambda handlers."""

import os
from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from utils.lambda_decorators import (
    lambda_handler,
    with_database,
    require_auth,
    validate_request_body,
    success_response,
    created_response,
    error_response,
    LambdaException,
)
from estoque.application.services.estoque_application_service import EstoqueApplicationService
from estoque.application.dto.estoque_dto import (
    EstoqueCreateDTO,
    EstoqueMovimentacaoDTO,
    EstoqueAjusteDTO,
)
from shared.domain.exceptions.base import ValidationException, BusinessRuleException

logger = structlog.get_logger()


# === INVENTORY CRUD HANDLERS ===

@lambda_handler
@with_database
@require_auth(permissions=["estoque:write"])
@validate_request_body(EstoqueCreateDTO)
async def create_inventory_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
    dto: EstoqueCreateDTO,
):
    """Handler for creating new inventory record."""
    try:
        service = EstoqueApplicationService(db)
        inventory_response = await service.create_inventory(dto)
        return created_response(inventory_response.dict())

    except ValidationException as e:
        raise LambdaException(400, e.message)
    except BusinessRuleException as e:
        raise LambdaException(409, e.message)
    except Exception as e:
        logger.error("Create inventory error", error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_database
@require_auth(permissions=["estoque:read"])
async def get_inventory_by_product_handler(
    event,
    context,
    body,
    path_params,
    query_params,
    db: AsyncSession,
    user_info: dict,
):
    """Handler for getting inventory by product ID."""
    produto_id = path_params.get("produto_id")
    if not produto_id:
        raise LambdaException(400, "produto_id is required")

    try:
        produto_uuid = UUID(produto_id)
    except ValueError:
        raise LambdaException(400, "Invalid produto_id format")

    try:
        service = EstoqueApplicationService(db)
        inventory = await service.get_inventory_by_product_id(produto_uuid)
        if not inventory:
            raise LambdaException(404, f"Inventory not found for product: {produto_id}")
        return success_response(inventory.dict())

    except LambdaException:
        raise
