"""API Schemas模块。

导出所有API相关的Pydantic模型。
"""

from .agent_schema import (
    AgentResponse,
    CreateAgentRequest,
    ListAgentsResponse,
    RegenerateApiKeyResponse,
    RegisterAgentRequest,
    RegisterAgentResponse,
    UpdateAgentRequest,
)
from .contact_schema import (
    AddContactRequest,
    ContactResponse,
    ListContactsResponse,
    UpdateContactRequest,
)
from .response import ApiResponse, ErrorDetail, ErrorResponse

__all__ = [
    "ApiResponse",
    "ErrorDetail",
    "ErrorResponse",
    "AgentResponse",
    "RegisterAgentRequest",
    "RegisterAgentResponse",
    "CreateAgentRequest",
    "UpdateAgentRequest",
    "ListAgentsResponse",
    "RegenerateApiKeyResponse",
    "AddContactRequest",
    "UpdateContactRequest",
    "ContactResponse",
    "ListContactsResponse",
]
