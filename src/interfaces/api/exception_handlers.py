"""全局异常处理器。

处理应用中的所有异常，返回统一的错误响应。
"""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.domain.shared.exceptions import DomainException


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """处理领域异常。

    Args:
        request: FastAPI请求对象
        exc: 领域异常

    Returns:
        JSON响应
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": 400,
            "status": 400,
            "message": exc.message,
            "data": None,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError | ValidationError
) -> JSONResponse:
    """处理验证异常。

    Args:
        request: FastAPI请求对象
        exc: 验证异常

    Returns:
        JSON响应
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "code": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "status": 422,
            "message": "Validation error",
            "details": errors,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理通用异常。

    Args:
        request: FastAPI请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "status": 500,
            "message": "Internal server error",
            "data": None,
        },
    )


def register_exception_handlers(app: Any) -> None:
    """注册所有异常处理器。

    Args:
        app: FastAPI应用实例
    """
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
