"""统一API响应格式。

提供标准化的API响应结构。
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式。

    所有API端点都应该使用此格式返回响应。
    """

    code: int = Field(200, description="业务状态码")
    status: int = Field(200, description="HTTP状态码")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field("success", description="响应消息")

    @classmethod
    def success(cls, data: T, message: str = "success") -> "ApiResponse[T]":
        """创建成功响应。

        Args:
            data: 响应数据
            message: 响应消息

        Returns:
            成功的API响应
        """
        return cls(code=200, status=200, data=data, message=message)

    @classmethod
    def error(cls, code: int, message: str, status: int | None = None) -> "ApiResponse":
        """创建错误响应。

        Args:
            code: 业务错误码
            message: 错误消息
            status: HTTP状态码，默认与code相同

        Returns:
            错误的API响应
        """
        if status is None:
            status = code
        return cls(code=code, status=status, data=None, message=message)


class ErrorDetail(BaseModel):
    """错误详情。

    用于提供更详细的错误信息。
    """

    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")


class ErrorResponse(BaseModel):
    """错误响应格式。

    用于返回详细的错误信息。
    """

    code: int = Field(..., description="业务错误码")
    status: int = Field(..., description="HTTP状态码")
    message: str = Field(..., description="错误消息")
    details: Optional[list[ErrorDetail]] = Field(None, description="错误详情列表")
