"""Agent REST API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.agent.commands.create_agent_command import (
    CreateAgentCommand,
    CreateAgentCommandHandler,
)
from src.application.agent.commands.regenerate_api_key_command import (
    RegenerateApiKeyCommand,
    RegenerateApiKeyCommandHandler,
)
from src.application.agent.commands.register_agent_command import (
    RegisterAgentCommand,
    RegisterAgentCommandHandler,
)
from src.application.agent.commands.update_agent_command import (
    UpdateAgentCommand,
    UpdateAgentCommandHandler,
)
from src.application.agent.queries.get_agent_query import (
    GetAgentQuery,
    GetAgentQueryHandler,
)
from src.application.agent.queries.list_agents_query import (
    ListAgentsQuery,
    ListAgentsQueryHandler,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories.postgres_agent_repository import (
    PostgresAgentRepository,
)
from src.interfaces.api.schemas.agent_schema import (
    AgentResponse,
    CreateAgentRequest,
    ListAgentsResponse,
    RegenerateApiKeyResponse,
    RegisterAgentRequest,
    RegisterAgentResponse,
    UpdateAgentRequest,
)
from src.interfaces.api.schemas.response import ApiResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/register", response_model=ApiResponse[RegisterAgentResponse], status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: RegisterAgentRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Agent自主注册。

    返回Agent信息和API Key（仅此一次）。
    """
    agent_repo = PostgresAgentRepository(session)
    handler = RegisterAgentCommandHandler(agent_repo)

    command = RegisterAgentCommand(
        agent_id=request.agent_id,
        name=request.name,
        avatar=request.avatar,
        description=request.description,
        system_prompt=request.system_prompt,
        model_config=request.model_config.model_dump() if request.model_config else None,
    )

    result = await handler.handle(command)

    return ApiResponse(
        code=status.HTTP_201_CREATED,
        message="Agent registered successfully",
        data=RegisterAgentResponse(
            agent=result.agent.__dict__,
            api_key=result.api_key,
        ),
    )


@router.post("/{agent_id}/regenerate-key", response_model=ApiResponse[RegenerateApiKeyResponse])
async def regenerate_api_key(
    agent_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """重新生成Agent的API Key。

    返回新的API Key（仅此一次）。
    """
    agent_repo = PostgresAgentRepository(session)
    handler = RegenerateApiKeyCommandHandler(agent_repo)

    command = RegenerateApiKeyCommand(agent_id=agent_id)
    result = await handler.handle(command)

    return ApiResponse(
        code=status.HTTP_200_OK,
        message="API Key regenerated successfully",
        data=RegenerateApiKeyResponse(api_key=result.api_key),
    )


@router.post("", response_model=ApiResponse[AgentResponse], status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: CreateAgentRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """创建Agent（管理员）。"""
    agent_repo = PostgresAgentRepository(session)
    handler = CreateAgentCommandHandler(agent_repo)

    command = CreateAgentCommand(
        agent_id=request.agent_id,
        name=request.name,
        avatar=request.avatar,
        description=request.description,
        system_prompt=request.system_prompt,
        model_config=request.model_config.model_dump() if request.model_config else None,
    )

    result = await handler.handle(command)

    return ApiResponse(
        code=status.HTTP_201_CREATED,
        message="Agent created successfully",
        data=AgentResponse(**result.__dict__),
    )


@router.get("", response_model=ApiResponse[ListAgentsResponse])
async def list_agents(
    is_active: Optional[bool] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """获取Agent列表。"""
    agent_repo = PostgresAgentRepository(session)
    handler = ListAgentsQueryHandler(agent_repo)

    query = ListAgentsQuery(
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    result = await handler.handle(query)

    return ApiResponse(
        code=status.HTTP_200_OK,
        message="Agents retrieved successfully",
        data=ListAgentsResponse(
            items=[AgentResponse(**item.__dict__) for item in result.items],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        ),
    )


@router.get("/{agent_id}", response_model=ApiResponse[AgentResponse])
async def get_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """获取Agent详情。"""
    agent_repo = PostgresAgentRepository(session)
    handler = GetAgentQueryHandler(agent_repo)

    query = GetAgentQuery(agent_id=agent_id)
    result = await handler.handle(query)

    return ApiResponse(
        code=status.HTTP_200_OK,
        message="Agent retrieved successfully",
        data=AgentResponse(**result.__dict__),
    )


@router.put("/{agent_id}", response_model=ApiResponse[AgentResponse])
async def update_agent(
    agent_id: UUID,
    request: UpdateAgentRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """更新Agent信息。"""
    agent_repo = PostgresAgentRepository(session)
    handler = UpdateAgentCommandHandler(agent_repo)

    command = UpdateAgentCommand(
        agent_id=agent_id,
        name=request.name,
        avatar=request.avatar,
        description=request.description,
        system_prompt=request.system_prompt,
        model_config=request.model_config.model_dump() if request.model_config else None,
    )

    result = await handler.handle(command)

    return ApiResponse(
        code=status.HTTP_200_OK,
        message="Agent updated successfully",
        data=AgentResponse(**result.__dict__),
    )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """删除Agent。"""
    agent_repo = PostgresAgentRepository(session)
    await agent_repo.delete(agent_id)
