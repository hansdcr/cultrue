"""Contact REST API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.contact.commands.add_contact_command import (
    AddContactCommand,
    AddContactCommandHandler,
)
from src.application.contact.commands.remove_contact_command import (
    RemoveContactCommand,
    RemoveContactCommandHandler,
)
from src.application.contact.commands.update_contact_command import (
    UpdateContactCommand,
    UpdateContactCommandHandler,
)
from src.application.contact.queries.get_contacts_query import (
    GetContactsQuery,
    GetContactsQueryHandler,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories.postgres_contact_repository import (
    PostgresContactRepository,
)
from src.infrastructure.persistence.repositories.postgres_participant_repository import (
    PostgresParticipantRepository,
)
from src.interfaces.api.schemas.contact_schema import (
    AddContactRequest,
    ContactResponse,
    ListContactsResponse,
    UpdateContactRequest,
)
from src.interfaces.api.schemas.response import ApiResponse

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("", response_model=ApiResponse[ContactResponse], status_code=status.HTTP_201_CREATED)
async def add_contact(
    request: AddContactRequest,
    owner_type: str = Query(..., description="拥有者类型: user or agent"),
    owner_id: UUID = Query(..., description="拥有者ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """添加联系人。"""
    participant_repo = PostgresParticipantRepository(session)
    contact_repo = PostgresContactRepository(session, participant_repo)
    handler = AddContactCommandHandler(contact_repo)

    command = AddContactCommand(
        owner_type=owner_type,
        owner_id=owner_id,
        target_type=request.target_type,
        target_id=UUID(request.target_id),
        contact_type=request.contact_type,
        alias=request.alias,
    )

    result = await handler.handle(command)

    return ApiResponse(
        code=status.HTTP_201_CREATED,
        message="Contact added successfully",
        data=ContactResponse(**result.__dict__),
    )


@router.get("", response_model=ApiResponse[ListContactsResponse])
async def get_contacts(
    owner_type: str = Query(..., description="拥有者类型: user or agent"),
    owner_id: UUID = Query(..., description="拥有者ID"),
    contact_type: Optional[str] = Query(default=None, description="联系人类型过滤"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """获取联系人列表。"""
    participant_repo = PostgresParticipantRepository(session)
    contact_repo = PostgresContactRepository(session, participant_repo)
    handler = GetContactsQueryHandler(contact_repo)

    query = GetContactsQuery(
        owner_type=owner_type,
        owner_id=owner_id,
        contact_type=contact_type,
        limit=limit,
        offset=offset,
    )

    result = await handler.handle(query)

    return ApiResponse(
        code=status.HTTP_200_OK,
        message="Contacts retrieved successfully",
        data=ListContactsResponse(
            items=[ContactResponse(**item.__dict__) for item in result.items],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        ),
    )


@router.put("/{contact_id}", response_model=ApiResponse[ContactResponse])
async def update_contact(
    contact_id: UUID,
    request: UpdateContactRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """更新联系人。"""
    participant_repo = PostgresParticipantRepository(session)
    contact_repo = PostgresContactRepository(session, participant_repo)
    handler = UpdateContactCommandHandler(contact_repo)

    command = UpdateContactCommand(
        contact_id=contact_id,
        alias=request.alias,
        is_favorite=request.is_favorite,
    )

    result = await handler.handle(command)

    return ApiResponse(
        code=status.HTTP_200_OK,
        message="Contact updated successfully",
        data=ContactResponse(**result.__dict__),
    )


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
    contact_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """删除联系人。"""
    participant_repo = PostgresParticipantRepository(session)
    contact_repo = PostgresContactRepository(session, participant_repo)
    handler = RemoveContactCommandHandler(contact_repo)

    command = RemoveContactCommand(contact_id=contact_id)
    await handler.handle(command)
