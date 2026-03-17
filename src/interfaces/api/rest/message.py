"""Message API路由."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.messaging.commands.delete_message_command import (
    DeleteMessageCommand,
    DeleteMessageCommandHandler,
)
from src.application.messaging.commands.send_message_command import (
    SendMessageCommand,
    SendMessageCommandHandler,
)
from src.application.messaging.queries.get_message_query import (
    GetMessageQuery,
    GetMessageQueryHandler,
)
from src.application.messaging.queries.list_messages_query import (
    ListMessagesQuery,
    ListMessagesQueryHandler,
)
from src.domain.shared.exceptions import DomainException, NotFoundException
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
)
from src.infrastructure.persistence.repositories.postgres_message_repository import (
    PostgresMessageRepository,
)
from src.interfaces.api.dependencies import CurrentActor
from src.interfaces.api.schemas.message_schema import (
    MessageListResponse,
    MessageResponse,
    SendMessageRequest,
)
from src.interfaces.api.schemas.response import ApiResponse

router = APIRouter(prefix="/api", tags=["消息"])


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[MessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="发送消息",
    description="在指定会话中发送消息",
)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[MessageResponse]:
    """发送消息。

    Args:
        conversation_id: 会话ID
        request: 发送消息请求
        current_actor: 当前Actor
        db: 数据库会话

    Returns:
        发送的消息信息

    Raises:
        HTTPException: 如果发送失败
    """
    try:
        # 创建仓储和命令处理器
        message_repository = PostgresMessageRepository(db)
        conversation_repository = PostgresConversationRepository(db)
        handler = SendMessageCommandHandler(
            message_repository, conversation_repository
        )

        # 创建命令
        command = SendMessageCommand(
            conversation_id=conversation_id,
            sender=current_actor,
            message_type=request.message_type,
            content=request.content,
            metadata=request.metadata,
        )

        # 执行命令
        message_dto = await handler.handle(command)

        # 提交事务
        await db.commit()

        # 转换为响应
        response = MessageResponse(
            id=message_dto.id,
            conversation_id=message_dto.conversation_id,
            sender={
                "actor_type": message_dto.sender.actor_type,
                "actor_id": message_dto.sender.actor_id,
            },
            message_type=message_dto.message_type,
            content=message_dto.content,
            metadata=message_dto.metadata,
            created_at=message_dto.created_at,
        )

        return ApiResponse.success(
            data=response,
            message="Message sent successfully",
        )

    except (NotFoundException, DomainException) as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[MessageListResponse],
    summary="获取消息列表",
    description="获取指定会话的消息列表",
)
async def list_messages(
    conversation_id: UUID,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> ApiResponse[MessageListResponse]:
    """获取消息列表。

    Args:
        conversation_id: 会话ID
        current_actor: 当前Actor
        db: 数据库会话
        limit: 每页数量
        offset: 偏移量

    Returns:
        消息列表

    Raises:
        HTTPException: 如果查询失败
    """
    try:
        # 创建仓储和查询处理器
        message_repository = PostgresMessageRepository(db)
        handler = ListMessagesQueryHandler(message_repository)

        # 创建查询
        query = ListMessagesQuery(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )

        # 执行查询
        message_dtos = await handler.handle(query)

        # 转换为响应
        items = [
            MessageResponse(
                id=dto.id,
                conversation_id=dto.conversation_id,
                sender={
                    "actor_type": dto.sender.actor_type,
                    "actor_id": dto.sender.actor_id,
                },
                message_type=dto.message_type,
                content=dto.content,
                metadata=dto.metadata,
                created_at=dto.created_at,
            )
            for dto in message_dtos
        ]

        response = MessageListResponse(
            items=items,
            total=len(items),  # TODO: 实现总数查询
            limit=limit,
            offset=offset,
        )

        return ApiResponse.success(
            data=response,
            message="Messages retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/messages/{message_id}",
    response_model=ApiResponse[MessageResponse],
    summary="获取消息详情",
    description="根据消息ID获取消息详情",
)
async def get_message(
    message_id: UUID,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[MessageResponse]:
    """获取消息详情。

    Args:
        message_id: 消息ID
        current_actor: 当前Actor
        db: 数据库会话

    Returns:
        消息详情

    Raises:
        HTTPException: 如果消息不存在
    """
    try:
        # 创建仓储和查询处理器
        message_repository = PostgresMessageRepository(db)
        handler = GetMessageQueryHandler(message_repository)

        # 创建查询
        query = GetMessageQuery(message_id=message_id)

        # 执行查询
        message_dto = await handler.handle(query)

        # 转换为响应
        response = MessageResponse(
            id=message_dto.id,
            conversation_id=message_dto.conversation_id,
            sender={
                "actor_type": message_dto.sender.actor_type,
                "actor_id": message_dto.sender.actor_id,
            },
            message_type=message_dto.message_type,
            content=message_dto.content,
            metadata=message_dto.metadata,
            created_at=message_dto.created_at,
        )

        return ApiResponse.success(
            data=response,
            message="Message retrieved successfully",
        )

    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除消息",
    description="删除指定消息(仅发送者可删除)",
)
async def delete_message(
    message_id: UUID,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """删除消息。

    Args:
        message_id: 消息ID
        current_actor: 当前Actor
        db: 数据库会话

    Raises:
        HTTPException: 如果删除失败
    """
    try:
        # 创建仓储和命令处理器
        message_repository = PostgresMessageRepository(db)
        handler = DeleteMessageCommandHandler(message_repository)

        # 创建命令
        command = DeleteMessageCommand(
            message_id=message_id,
            actor=current_actor,
        )

        # 执行命令
        await handler.handle(command)

        # 提交事务
        await db.commit()

    except (NotFoundException, DomainException) as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
