"""地图REST API routes。"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.map.commands.create_agent_location_command import (
    CreateAgentLocationCommand,
    CreateAgentLocationCommandHandler,
)
from src.application.map.commands.update_agent_location_command import (
    UpdateAgentLocationCommand,
    UpdateAgentLocationCommandHandler,
)
from src.application.map.commands.delete_agent_location_command import (
    DeleteAgentLocationCommand,
    DeleteAgentLocationCommandHandler,
)
from src.application.map.queries.get_nearby_agents_query import (
    GetNearbyAgentsQuery,
    GetNearbyAgentsQueryHandler,
)
from src.application.map.queries.get_agent_location_query import (
    GetAgentLocationQuery,
    GetAgentLocationQueryHandler,
)
from src.application.map.queries.get_agent_locations_query import (
    GetAgentLocationsQuery,
    GetAgentLocationsQueryHandler,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories.postgres_agent_location_repository import (
    PostgresAgentLocationRepository,
)
from src.infrastructure.persistence.repositories.postgres_agent_repository import (
    PostgresAgentRepository,
)
from src.interfaces.api.schemas.agent_location_schema import (
    CreateAgentLocationRequest,
    UpdateAgentLocationRequest,
    AgentLocationResponse,
    NearbyAgentsResponse,
    AgentLocationsResponse,
    AgentInfoSchema,
)
from src.interfaces.api.schemas.response import ApiResponse
from src.interfaces.api.dependencies import CurrentAdmin

router = APIRouter(prefix="/map", tags=["map"])


@router.post(
    "/agent-locations",
    response_model=ApiResponse[AgentLocationResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_agent_location(
    request: CreateAgentLocationRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: CurrentAdmin = None,  # 管理员权限验证
):
    """创建Agent位置（管理员权限）。

    在地图上为Agent添加一个地理位置。
    """
    agent_repo = PostgresAgentRepository(session)
    location_repo = PostgresAgentLocationRepository(session, agent_repo)
    handler = CreateAgentLocationCommandHandler(location_repo, agent_repo)

    try:
        command = CreateAgentLocationCommand(
            agent_id=UUID(request.agent_id),
            latitude=request.latitude,
            longitude=request.longitude,
            address=request.address,
            is_active=request.is_active,
            display_order=request.display_order,
            metadata=request.metadata,
        )

        result = await handler.handle(command)

        return ApiResponse(
            code=status.HTTP_201_CREATED,
            message="Agent location created successfully",
            data=AgentLocationResponse(
                location_id=result.location_id,
                agent=AgentInfoSchema(
                    id=result.agent.id,
                    agent_id=result.agent.agent_id,
                    name=result.agent.name,
                    avatar=result.agent.avatar,
                    description=result.agent.description,
                ),
                latitude=result.latitude,
                longitude=result.longitude,
                address=result.address,
                is_active=result.is_active,
                display_order=result.display_order,
                distance=result.distance,
                created_at=result.created_at,
                updated_at=result.updated_at,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/nearby",
    response_model=ApiResponse[NearbyAgentsResponse]
)
async def get_nearby_agents(
    latitude: float = Query(..., ge=-90, le=90, description="纬度"),
    longitude: float = Query(..., ge=-180, le=180, description="经度"),
    radius: int = Query(5000, ge=100, le=50000, description="半径（米）"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    session: AsyncSession = Depends(get_db_session),
):
    """查询周边Agent。

    根据用户当前位置查询周边的Agent。
    """
    agent_repo = PostgresAgentRepository(session)
    location_repo = PostgresAgentLocationRepository(session, agent_repo)
    handler = GetNearbyAgentsQueryHandler(location_repo)

    query = GetNearbyAgentsQuery(
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        limit=limit,
        only_active=True,
    )

    result = await handler.handle(query)

    return ApiResponse(
        code=status.HTTP_200_OK,
        message="Nearby agents retrieved successfully",
        data=NearbyAgentsResponse(
            items=[
                AgentLocationResponse(
                    location_id=item.location_id,
                    agent=AgentInfoSchema(
                        id=item.agent.id,
                        agent_id=item.agent.agent_id,
                        name=item.agent.name,
                        avatar=item.agent.avatar,
                        description=item.agent.description,
                    ),
                    latitude=item.latitude,
                    longitude=item.longitude,
                    address=item.address,
                    is_active=item.is_active,
                    display_order=item.display_order,
                    distance=item.distance,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in result.items
            ],
            total=result.total,
            center=result.center,
            radius=result.radius,
        ),
    )


@router.get(
    "/agents/{agent_id}/locations",
    response_model=ApiResponse[AgentLocationsResponse]
)
async def get_agent_locations(
    agent_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取Agent的所有位置。

    查询某个Agent在地图上的所有位置。
    """
    agent_repo = PostgresAgentRepository(session)
    location_repo = PostgresAgentLocationRepository(session, agent_repo)
    handler = GetAgentLocationsQueryHandler(location_repo, agent_repo)

    try:
        query = GetAgentLocationsQuery(
            agent_id=UUID(agent_id),
            only_active=True,
        )

        result = await handler.handle(query)

        return ApiResponse(
            code=status.HTTP_200_OK,
            message="Agent locations retrieved successfully",
            data=AgentLocationsResponse(
                items=[
                    AgentLocationResponse(
                        location_id=item.location_id,
                        agent=AgentInfoSchema(
                            id=item.agent.id,
                            agent_id=item.agent.agent_id,
                            name=item.agent.name,
                            avatar=item.agent.avatar,
                            description=item.agent.description,
                        ),
                        latitude=item.latitude,
                        longitude=item.longitude,
                        address=item.address,
                        is_active=item.is_active,
                        display_order=item.display_order,
                        distance=item.distance,
                        created_at=item.created_at,
                        updated_at=item.updated_at,
                    )
                    for item in result.items
                ],
                total=result.total,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/agent-locations/{location_id}",
    response_model=ApiResponse[AgentLocationResponse]
)
async def get_agent_location(
    location_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取Agent位置详情。

    根据位置ID查询位置的详细信息。
    """
    agent_repo = PostgresAgentRepository(session)
    location_repo = PostgresAgentLocationRepository(session, agent_repo)
    handler = GetAgentLocationQueryHandler(location_repo, agent_repo)

    try:
        query = GetAgentLocationQuery(location_id=UUID(location_id))
        result = await handler.handle(query)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location not found: {location_id}"
            )

        return ApiResponse(
            code=status.HTTP_200_OK,
            message="Agent location retrieved successfully",
            data=AgentLocationResponse(
                location_id=result.location_id,
                agent=AgentInfoSchema(
                    id=result.agent.id,
                    agent_id=result.agent.agent_id,
                    name=result.agent.name,
                    avatar=result.agent.avatar,
                    description=result.agent.description,
                ),
                latitude=result.latitude,
                longitude=result.longitude,
                address=result.address,
                is_active=result.is_active,
                display_order=result.display_order,
                distance=result.distance,
                created_at=result.created_at,
                updated_at=result.updated_at,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/agent-locations/{location_id}",
    response_model=ApiResponse[AgentLocationResponse]
)
async def update_agent_location(
    location_id: str,
    request: UpdateAgentLocationRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: CurrentAdmin = None,  # 管理员权限验证
):
    """更新Agent位置（管理员权限）。

    更新Agent在地图上的位置信息。
    """
    agent_repo = PostgresAgentRepository(session)
    location_repo = PostgresAgentLocationRepository(session, agent_repo)
    handler = UpdateAgentLocationCommandHandler(location_repo, agent_repo)

    try:
        command = UpdateAgentLocationCommand(
            location_id=UUID(location_id),
            latitude=request.latitude,
            longitude=request.longitude,
            address=request.address,
            is_active=request.is_active,
            display_order=request.display_order,
            metadata=request.metadata,
        )

        result = await handler.handle(command)

        return ApiResponse(
            code=status.HTTP_200_OK,
            message="Agent location updated successfully",
            data=AgentLocationResponse(
                location_id=result.location_id,
                agent=AgentInfoSchema(
                    id=result.agent.id,
                    agent_id=result.agent.agent_id,
                    name=result.agent.name,
                    avatar=result.agent.avatar,
                    description=result.agent.description,
                ),
                latitude=result.latitude,
                longitude=result.longitude,
                address=result.address,
                is_active=result.is_active,
                display_order=result.display_order,
                distance=result.distance,
                created_at=result.created_at,
                updated_at=result.updated_at,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/agent-locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_agent_location(
    location_id: str,
    session: AsyncSession = Depends(get_db_session),
    admin: CurrentAdmin = None,  # 管理员权限验证
):
    """删除Agent位置（管理员权限）。

    从地图上删除Agent的位置。
    """
    location_repo = PostgresAgentLocationRepository(
        session, PostgresAgentRepository(session)
    )
    handler = DeleteAgentLocationCommandHandler(location_repo)

    try:
        command = DeleteAgentLocationCommand(location_id=UUID(location_id))
        await handler.handle(command)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

