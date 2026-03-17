"""Conversation API路由."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.messaging.commands.add_member_command import (
    AddMemberCommand,
    AddMemberCommandHandler,
)
from src.application.messaging.commands.archive_conversation_command import (
    ArchiveConversationCommand,
    ArchiveConversationCommandHandler,
)
from src.application.messaging.commands.create_conversation_command import (
    CreateConversationCommand,
    CreateConversationCommandHandler,
)
from src.application.messaging.commands.remove_member_command import (
    RemoveMemberCommand,
    RemoveMemberCommandHandler,
)
from src.application.messaging.queries.get_conversation_query import (
    GetConversationQuery,
    GetConversationQueryHandler,
)
from src.application.messaging.queries.list_conversations_query import (
    ListConversationsQuery,
    ListConversationsQueryHandler,
)
from src.domain.shared.exceptions import DomainException, NotFoundException
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
)
from src.interfaces.api.dependencies import CurrentActor
from src.interfaces.api.schemas.conversation_schema import (
    AddMemberRequest,
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    RemoveMemberRequest,
)
from src.interfaces.api.schemas.response import ApiResponse

router = APIRouter(prefix="/api/conversations", tags=["会话"])


@router.post(
    "",
    response_model=ApiResponse[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建会话",
    description="创建一对一会话或群聊",
)
async def create_conversation(
    request: CreateConversationRequest,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ConversationResponse]:
    """创建会话。

    Args:
        request: 创建会话请求
        current_actor: 当前Actor
        db: 数据库会话

    Returns:
        创建的会话信息

    Raises:
        HTTPException: 如果创建失败
    """
    try:
        # 创建仓储和命令处理器
        conversation_repository = PostgresConversationRepository(db)
        handler = CreateConversationCommandHandler(conversation_repository)

        # 将ActorSchema转换为Actor
        members = [
            Actor.from_user(UUID(m.actor_id)) if m.actor_type == "user"
            else Actor.from_agent(UUID(m.actor_id))
            for m in request.members
        ]

        # 创建命令
        command = CreateConversationCommand(
            conversation_type=request.conversation_type,
            members=members,
            title=request.title,
            creator=current_actor,
        )

        # 执行命令
        conversation_dto = await handler.handle(command)

        # 提交事务
        await db.commit()

        # 转换为响应
        response = ConversationResponse(
            id=conversation_dto.id,
            conversation_type=conversation_dto.conversation_type,
            status=conversation_dto.status,
            members=[
                {"actor_type": m.actor_type, "actor_id": m.actor_id}
                for m in conversation_dto.members
            ],
            message_count=conversation_dto.message_count,
            title=conversation_dto.title,
            last_message_at=conversation_dto.last_message_at,
            created_at=conversation_dto.created_at,
            updated_at=conversation_dto.updated_at,
        )

        return ApiResponse.success(
            data=response,
            message="Conversation created successfully",
        )

    except DomainException as e:
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

