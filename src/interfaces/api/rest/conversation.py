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



@router.get(
    "",
    response_model=ApiResponse[ConversationListResponse],
    summary="获取会话列表",
    description="获取当前Actor的会话列表",
)
async def list_conversations(
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> ApiResponse[ConversationListResponse]:
    """获取会话列表。

    Args:
        current_actor: 当前Actor
        db: 数据库会话
        limit: 每页数量
        offset: 偏移量

    Returns:
        会话列表

    Raises:
        HTTPException: 如果查询失败
    """
    try:
        # 创建仓储和查询处理器
        conversation_repository = PostgresConversationRepository(db)
        handler = ListConversationsQueryHandler(conversation_repository)

        # 创建查询
        query = ListConversationsQuery(
            actor=current_actor,
            limit=limit,
            offset=offset,
        )

        # 执行查询
        conversation_dtos = await handler.handle(query)

        # 转换为响应
        items = [
            ConversationResponse(
                id=dto.id,
                conversation_type=dto.conversation_type,
                status=dto.status,
                members=[
                    {"actor_type": m.actor_type, "actor_id": m.actor_id}
                    for m in dto.members
                ],
                message_count=dto.message_count,
                title=dto.title,
                last_message_at=dto.last_message_at,
                created_at=dto.created_at,
                updated_at=dto.updated_at,
            )
            for dto in conversation_dtos
        ]

        response = ConversationListResponse(
            items=items,
            total=len(items),  # TODO: 实现总数查询
            limit=limit,
            offset=offset,
        )

        return ApiResponse.success(
            data=response,
            message="Conversations retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/{conversation_id}",
    response_model=ApiResponse[ConversationResponse],
    summary="获取会话详情",
    description="根据会话ID获取会话详情",
)
async def get_conversation(
    conversation_id: UUID,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ConversationResponse]:
    """获取会话详情。

    Args:
        conversation_id: 会话ID
        current_actor: 当前Actor
        db: 数据库会话

    Returns:
        会话详情

    Raises:
        HTTPException: 如果会话不存在或无权访问
    """
    try:
        # 创建仓储和查询处理器
        conversation_repository = PostgresConversationRepository(db)
        handler = GetConversationQueryHandler(conversation_repository)

        # 创建查询
        query = GetConversationQuery(conversation_id=conversation_id)

        # 执行查询
        conversation_dto = await handler.handle(query)

        # 验证当前Actor是否为会话成员
        is_member = any(
            m.actor_type == current_actor.actor_type.value and
            m.actor_id == str(current_actor.actor_id)
            for m in conversation_dto.members
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this conversation",
            )

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
            message="Conversation retrieved successfully",
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


@router.post(
    "/{conversation_id}/members",
    response_model=ApiResponse[ConversationResponse],
    summary="添加成员",
    description="向群聊添加成员",
)
async def add_member(
    conversation_id: UUID,
    request: AddMemberRequest,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ConversationResponse]:
    """添加成员。

    Args:
        conversation_id: 会话ID
        request: 添加成员请求
        current_actor: 当前Actor
        db: 数据库会话

    Returns:
        更新后的会话信息

    Raises:
        HTTPException: 如果添加失败
    """
    try:
        # 创建仓储和命令处理器
        conversation_repository = PostgresConversationRepository(db)
        handler = AddMemberCommandHandler(conversation_repository)

        # 将ActorSchema转换为Actor
        member = (
            Actor.from_user(UUID(request.actor_id))
            if request.actor_type == "user"
            else Actor.from_agent(UUID(request.actor_id))
        )

        # 创建命令
        command = AddMemberCommand(
            conversation_id=conversation_id,
            member=member,
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
            message="Member added successfully",
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


@router.delete(
    "/{conversation_id}/members",
    response_model=ApiResponse[ConversationResponse],
    summary="移除成员",
    description="从群聊移除成员",
)
async def remove_member(
    conversation_id: UUID,
    request: RemoveMemberRequest,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ConversationResponse]:
    """移除成员。

    Args:
        conversation_id: 会话ID
        request: 移除成员请求
        current_actor: 当前Actor
        db: 数据库会话

    Returns:
        更新后的会话信息

    Raises:
        HTTPException: 如果移除失败
    """
    try:
        # 创建仓储和命令处理器
        conversation_repository = PostgresConversationRepository(db)
        handler = RemoveMemberCommandHandler(conversation_repository)

        # 将ActorSchema转换为Actor
        member = (
            Actor.from_user(UUID(request.actor_id))
            if request.actor_type == "user"
            else Actor.from_agent(UUID(request.actor_id))
        )

        # 创建命令
        command = RemoveMemberCommand(
            conversation_id=conversation_id,
            member=member,
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
            message="Member removed successfully",
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


@router.put(
    "/{conversation_id}/archive",
    response_model=ApiResponse[ConversationResponse],
    summary="归档会话",
    description="归档指定会话",
)
async def archive_conversation(
    conversation_id: UUID,
    current_actor: CurrentActor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ConversationResponse]:
    """归档会话。

    Args:
        conversation_id: 会话ID
        current_actor: 当前Actor
        db: 数据库会话

    Returns:
        归档后的会话信息

    Raises:
        HTTPException: 如果归档失败
    """
    try:
        # 创建仓储和命令处理器
        conversation_repository = PostgresConversationRepository(db)
        handler = ArchiveConversationCommandHandler(conversation_repository)

        # 创建命令
        command = ArchiveConversationCommand(conversation_id=conversation_id)

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
            message="Conversation archived successfully",
        )

    except NotFoundException as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
