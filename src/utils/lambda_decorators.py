# src/utils/lambda_decorators.py
"""Decorators para substituir FastAPI Depends em Lambda functions."""

import json
import functools
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.connection import get_async_session

logger = structlog.get_logger()


@dataclass
class LambdaResponse:
    status_code: int
    body: Dict[str, Any]
    headers: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "statusCode": self.status_code,
            "body": json.dumps(self.body, default=str),
            "headers": self.headers or {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
            },
        }
        return response


class LambdaException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def lambda_handler(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        import asyncio

        async def async_wrapper():
            try:
                body = json.loads(event["body"]) if event.get("body") else {}
                path_params = event.get("pathParameters") or {}
                query_params = event.get("queryStringParameters") or {}

                result = await func(event, context, body, path_params, query_params)

                if isinstance(result, LambdaResponse):
                    return result.to_dict()
                return LambdaResponse(200, result).to_dict()

            except LambdaException as e:
                return LambdaResponse(e.status_code, {"detail": e.detail}).to_dict()
            except Exception as e:
                logger.error("Lambda handler error", error=str(e))
                return LambdaResponse(500, {"detail": "Internal server error"}).to_dict()

        return asyncio.run(async_wrapper())

    return wrapper


def with_database(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async for db_session in get_async_session():
            try:
                kwargs["db"] = db_session
                result = await func(*args, **kwargs)
                await db_session.commit()
                return result
            except Exception:
                await db_session.rollback()
                raise
            finally:
                await db_session.close()

    return wrapper



def require_auth(permissions: Optional[List[str]] = None):
    """
    Substitui @with_auth + @require_permission(...).
    Se permissions for None ou vazio, só exige que o usuário esteja autenticado.
    Caso contrário, também checa cada permissão na lista.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs):
            # 1) extrai user_info do requestContext.authorizer
            auth_ctx = (event.get("requestContext") or {}).get("authorizer") or {}
            user_id = auth_ctx.get("userId")
            if not user_id:
                raise LambdaException(401, "Unauthorized")

            # monta o user_info
            perms_raw = auth_ctx.get("permissoes", "")
            perms = perms_raw.split(",") if perms_raw else []
            user_info = {
                "userId": user_id,
                "email": auth_ctx.get("email"),
                "permissoes": perms,
            }
            kwargs["user_info"] = user_info

            # 2) checa permissões, se fornecidas
            if permissions:
                allowed = False
                for req in permissions:
                    if req in perms or "admin:*" in perms:
                        allowed = True
                        break
                if not allowed:
                    raise LambdaException(403, f"Permission required: {permissions}")

            # 3) chama a função original
            try:
                return await func(event, context, *args, **kwargs)
            except LambdaException:
                raise
            except Exception as e:
                logger.error("Auth wrapper error", error=str(e))
                raise LambdaException(500, "Authentication error")

        return wrapper
    return decorator


def validate_request_body(dto_class):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(event, context, body, *args, **kwargs):
            try:
                dto = dto_class(**body)
                kwargs["dto"] = dto
                return await func(event, context, body, *args, **kwargs)
            except Exception as e:
                raise LambdaException(400, f"Invalid request body: {e}")

        return wrapper

    return decorator


def success_response(data: Any, status_code: int = 200) -> LambdaResponse:
    return LambdaResponse(status_code, data)


def error_response(message: str, status_code: int = 400) -> LambdaResponse:
    return LambdaResponse(status_code, {"detail": message})


def created_response(data: Any) -> LambdaResponse:
    return LambdaResponse(201, data)


def no_content_response() -> LambdaResponse:
    return LambdaResponse(204, {})
