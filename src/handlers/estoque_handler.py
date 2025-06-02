# src/handlers/estoque_handler.py
"""Estoque (Inventory) Lambda handlers."""

from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from utils.lambda_decorators import (
    lambda_handler, with_auth, require_permission, validate_request_body,
    success_response, created_response, error_response, LambdaException, with_database
)
from estoque.application.services.estoque_application_service import EstoqueApplicationService
from estoque.application.dto.estoque_dto import (
    EstoqueCreateDTO,
    EstoqueMovimentacaoDTO,
    EstoqueAjusteDTO
)
from shared.domain.exceptions.base import ValidationException, BusinessRuleException
# Imports necessários que faltaram
import os
from datetime import datetime

logger = structlog.get_logger()

# === INVENTORY CRUD HANDLERS ===

@lambda_handler
@with_auth
@require_permission("estoque:write")
@validate_request_body(EstoqueCreateDTO)
async def create_inventory_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession, dto: EstoqueCreateDTO
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
@with_auth
@require_permission("estoque:read")
async def get_inventory_by_product_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession
):
    """Handler for getting inventory by product ID."""
    try:
        produto_id = path_params.get("produto_id")
        if not produto_id:
            raise LambdaException(400, "produto_id is required")
        
        # Validate UUID
        try:
            produto_uuid = UUID(produto_id)
        except ValueError:
            raise LambdaException(400, "Invalid produto_id format")
        
        service = EstoqueApplicationService(db)
        inventory = await service.get_inventory_by_product_id(produto_uuid)
        
        if not inventory:
            raise LambdaException(404, f"Inventory not found for product: {produto_id}")
        
        return success_response(inventory.dict())
        
    except LambdaException:
        raise
    except Exception as e:
        logger.error("Get inventory by product error", produto_id=produto_id, error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_auth
@require_permission("estoque:read")
async def list_inventory_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession
):
    """Handler for listing all inventory with pagination."""
    try:
        # Parse pagination parameters
        skip = int(query_params.get("skip", 0))
        limit = int(query_params.get("limit", 100))
        
        # Validate pagination
        if skip < 0:
            raise LambdaException(400, "skip must be >= 0")
        if limit < 1 or limit > 1000:
            raise LambdaException(400, "limit must be between 1 and 1000")
        
        service = EstoqueApplicationService(db)
        inventory_list = await service.get_all_inventory(skip, limit)
        
        return success_response(inventory_list.dict())
        
    except LambdaException:
        raise
    except Exception as e:
        logger.error("List inventory error", error=str(e))
        raise LambdaException(500, "Internal server error")


# === STOCK MOVEMENT HANDLERS ===

@lambda_handler
@with_auth
@with_database
@require_permission("estoque:write")
@validate_request_body(EstoqueMovimentacaoDTO)
async def add_stock_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession, dto: EstoqueMovimentacaoDTO
):
    """Handler for adding stock to product."""
    try:
        service = EstoqueApplicationService(db)
        inventory_response = await service.add_stock(dto)
        
        return success_response(inventory_response.dict())
        
    except ValidationException as e:
        raise LambdaException(400, e.message)
    except BusinessRuleException as e:
        raise LambdaException(409, e.message)
    except Exception as e:
        logger.error("Add stock error", error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_auth
@require_permission("estoque:write")
@validate_request_body(EstoqueMovimentacaoDTO)
async def remove_stock_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession, dto: EstoqueMovimentacaoDTO
):
    """Handler for removing stock from product."""
    try:
        service = EstoqueApplicationService(db)
        inventory_response = await service.remove_stock(dto)
        
        return success_response(inventory_response.dict())
        
    except ValidationException as e:
        raise LambdaException(400, e.message)
    except BusinessRuleException as e:
        raise LambdaException(409, e.message)
    except Exception as e:
        logger.error("Remove stock error", error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_auth
@require_permission("estoque:write")
@validate_request_body(EstoqueAjusteDTO)
async def adjust_stock_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession, dto: EstoqueAjusteDTO
):
    """Handler for adjusting stock to new quantity."""
    try:
        service = EstoqueApplicationService(db)
        inventory_response = await service.adjust_stock(dto)
        
        return success_response(inventory_response.dict())
        
    except ValidationException as e:
        raise LambdaException(400, e.message)
    except BusinessRuleException as e:
        raise LambdaException(409, e.message)
    except Exception as e:
        logger.error("Adjust stock error", error=str(e))
        raise LambdaException(500, "Internal server error")


# === REPORTS HANDLERS ===

@lambda_handler
@with_auth
@require_permission("estoque:read")
async def low_stock_report_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession
):
    """Handler for getting low stock report."""
    try:
        service = EstoqueApplicationService(db)
        report = await service.get_low_stock_report()
        
        return success_response(report.dict())
        
    except Exception as e:
        logger.error("Low stock report error", error=str(e))
        raise LambdaException(500, "Internal server error")


@lambda_handler
@with_auth
@require_permission("estoque:read")
async def out_of_stock_report_handler(
    event, context, body, path_params, query_params,
    current_user, db: AsyncSession
):
    """Handler for getting out of stock report."""
    try:
        service = EstoqueApplicationService(db)
        report = await service.get_out_of_stock_report()
        
        return success_response(report.dict())
        
    except Exception as e:
        logger.error("Out of stock report error", error=str(e))
        raise LambdaException(500, "Internal server error")


# === UTILITY HANDLERS ===

@lambda_handler
async def health_check_handler(event, context, body, path_params, query_params):
    """Health check endpoint."""
    return success_response({
        "status": "healthy",
        "service": "estoque-service",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    })


# # === ADDITIONAL HANDLERS (Se necessário) ===

# @lambda_handler
# @with_auth
# @require_permission("estoque:read")
# async def get_inventory_summary_handler(
#     event, context, body, path_params, query_params,
#     current_user, db: AsyncSession
# ):
#     """Handler for getting inventory summary/dashboard."""
#     try:
#         service = EstoqueApplicationService(db)
        
#         # Buscar dados para summary
#         total_items = await service.count_total_inventory_items()
#         low_stock_count = len((await service.get_low_stock_report()).produtos)
#         out_of_stock_count = len((await service.get_out_of_stock_report()).produtos)
        
#         summary = {
#             "total_items": total_items,
#             "low_stock_items": low_stock_count,
#             "out_of_stock_items": out_of_stock_count,
#             "healthy_stock_items": total_items - low_stock_count - out_of_stock_count,
#             "generated_at": datetime.utcnow().isoformat()
#         }
        
#         return success_response(summary)
        
#     except Exception as e:
#         logger.error("Inventory summary error", error=str(e))
#         raise LambdaException(500, "Internal server error")


