"""
Pydantic models for the TriAI messaging server.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageRequest(BaseModel):
    """Request model for sending messages."""
    user_to: str
    message: str


class MessageResponse(BaseModel):
    """Response model for message data."""
    message_id: int
    posted: datetime
    user_from: str
    user_to: str
    message: str
    user_read: Optional[datetime] = None


class AgentInfo(BaseModel):
    """Model for agent information."""
    agent: str
    description: str
    model_api: str
    model: str


class MCPRequest(BaseModel):
    """Request model for MCP tool calls."""
    tool: str
    parameters: Dict[str, Any]


class MCPResponse(BaseModel):
    """Response model for MCP tool results."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MemoryRequest(BaseModel):
    """Request model for storing memories."""
    agent_name: str
    memory_label: str
    memory_content: str
    related_to_tags: str
    purge_after: Optional[datetime] = None


class MemoryResponse(BaseModel):
    """Response model for memory data."""
    memory_id: int
    agent: str
    first_posted: datetime
    times_recalled: int
    last_recalled: Optional[datetime]
    memory_label: str
    memory: str
    related_to: str
    purge_after: Optional[datetime]


class QueryHistoryResponse(BaseModel):
    """Response model for query history."""
    query_id: int
    agent: str
    database_name: str
    sql_query: str
    executed_time: datetime
    row_count: int
    execution_time_ms: int


class DatabaseConnectionRequest(BaseModel):
    """Request model for database connections."""
    server_instance: str
    database_name: str
    connection_string: Optional[str] = None


class QueryRequest(BaseModel):
    """Request model for SQL queries."""
    database_name: str
    sql_query: str
    row_limit: Optional[int] = 1000


class TableSampleRequest(BaseModel):
    """Request model for table sampling."""
    database_name: str
    table_name: str
    row_count: Optional[int] = 10
    columns: Optional[List[str]] = None


class PermissionCheckRequest(BaseModel):
    """Request model for permission checking."""
    database_name: str
    object_name: str
    operation: str  # SELECT, INSERT, UPDATE, DELETE