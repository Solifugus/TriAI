# TriAI Framework Design Document

## Overview

TriAI is an AI framework built on three core components that work together to 
provide multi-agent AI capabilities with database integration.

### Architecture Components

- **Messaging Server** - Central hub for communication and MCP tool serving
- **Browser Client** - Web-based user interface for agent interaction  
- **Agent Server** - AI agents that process messages and execute tasks

---

## Agent Server

### Agent Management
Agents operate on a turn-based polling system where each agent independently 
checks for and responds to its messages. Users send messages to one specific 
agent at a time (no broadcasting). Agents are unaware of other agents' 
activities and operate independently.

### Agent Polling Cycle
1. Agent wakes up on its scheduled interval
2. Checks for unread messages directed to it
3. Processes and responds to messages using MCP tools
4. Updates message read status
5. Goes back to sleep until next cycle

### Agent Lifecycle Management
- Agents connect to messaging server via WebSocket on startup
- Agent identification and configuration loaded from AI_Agents table using 
DataLink
- Agents maintain persistent WebSocket connection for MCP tool access
- Agent registration verified against AI_Agents table on connection

### Agent-Server Communication
- **WebSocket Protocol**: Agents connect to `/ws/agent/{agent_name}`
- **MCP Tool Access**: All MCP tools provided via WebSocket messaging
- **Message Polling**: Agents request message checks through WebSocket
- **Connection Recovery**: Agents automatically reconnect on disconnection

### Model Support
The framework supports multiple AI model providers:
- **Ollama** (local, default: qwen2.5-coder model)
- **Microsoft 365 Copilot API**
- **OpenAI API**
- **Anthropic API**

Configuration is managed through `config.yaml` containing model settings, API 
keys, and database connection parameters.

### Database Schema

#### AI_Agents Table
```sql
CREATE TABLE AI_Agents (
    Agent         VARCHAR(15) NOT NULL,
    Description   VARCHAR(MAX),
    Model_API     VARCHAR(30),
    Model         VARCHAR(100),
    Model_API_KEY VARCHAR(500),
    CONSTRAINT PK_AI_Agents PRIMARY KEY (Agent)
);
```

#### AI_Memories Table
```sql
CREATE TABLE AI_Memories (
    Memory_ID      INT IDENTITY(1,1) NOT NULL,
    Agent          VARCHAR(15) NOT NULL,
    First_Posted   DATETIME NOT NULL DEFAULT GETDATE(),
    Times_Recalled INT NOT NULL DEFAULT 0,
    Last_Recalled  DATETIME,
    Memory_Label   VARCHAR(100) NOT NULL,
    Memory         VARCHAR(MAX),
    Related_To     VARCHAR(200) NOT NULL,
    Purge_After    DATETIME,
    CONSTRAINT PK_AI_Memories PRIMARY KEY (Memory_ID),
    CONSTRAINT FK_AI_Memories_Agent FOREIGN KEY (Agent) REFERENCES 
AI_Agents(Agent)
);
```

**Note**: `Related_To` contains space-separated tags for memory categorization 
and retrieval.

---

## Browser Client

### User Interface
- Clean, blue-themed interface built with vanilla HTML, CSS, and JavaScript
- Large chat window for natural conversation flow
- Agent selection dropdown populated via REST API call
- Tabular display capability for database query results
- User identification via REST API call
- Transactional messaging (no session management)

### Features
- One-to-one messaging with selected AI agents (no broadcast messaging)
- Query result visualization in tabular format
- Agent list retrieval with descriptions
- Responsive design for various screen sizes

### REST API Endpoints Required
- **GET /api/user** - Returns current user name
- **GET /api/agents** - Returns list of available agents with descriptions
- **POST /api/message** - Send message to specific agent
- **GET /api/messages/{agent}** - Get conversation history with specific agent

---

## Messaging Server (Python FastAPI)

### Core Responsibilities
- Serves static web files from `/public` folder via HTTP
- Provides REST APIs for browser client communication using FastAPI
- Handles WebSocket connections for agent communication
- Provides MCP tool services to agents via WebSocket
- Mediates message storage and retrieval between users and AI agents
- Handles transactional messaging (no session state maintenance)

### FastAPI Implementation
Built using Python FastAPI framework for high-performance async REST APIs and 
WebSocket support with automatic OpenAPI documentation.

### REST API Endpoints

#### User & Agent Management
```python
@app.get("/api/user")
async def get_current_user() -> dict:
    """Returns current user identification (hardcoded for now)"""
    return {"username": "testuser"}
    
@app.get("/api/agents")
async def get_agents() -> List[dict]:
    """Returns available agents with descriptions from AI_Agents table"""
```

#### Messaging
```python
@app.post("/api/message")
async def send_message(message: MessageRequest) -> dict:
    """Accepts user messages for specific agents"""
    
@app.get("/api/messages/{agent}")
async def get_messages(agent: str, limit: int = 50) -> List[dict]:
    """Returns conversation history with specific agent"""
```

#### WebSocket for Agent Communication
```python
@app.websocket("/ws/agent/{agent_name}")
async def agent_websocket(websocket: WebSocket, agent_name: str):
    """WebSocket endpoint for agent connections and MCP tool access"""
```

#### Static File Serving
```python
app.mount("/", StaticFiles(directory="public", html=True), name="static")
```

### Data Models
```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageRequest(BaseModel):
    user_to: str
    message: str
    
class MessageResponse(BaseModel):
    message_id: int
    posted: datetime
    user_from: str
    user_to: str
    message: str
    user_read: Optional[datetime] = None

class AgentInfo(BaseModel):
    agent: str
    description: str
    model_api: str
    model: str

class MCPRequest(BaseModel):
    tool: str
    parameters: dict
    
class MCPResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
```

### MCP Tool Services
MCP tools are implemented as part of the messaging server and provided to agents 
via WebSocket connections. All tools use the shared DataLink instance for 
database operations.

### Dependencies
- **FastAPI** - Modern Python web framework
- **websockets** - WebSocket support for agent communication
- **uvicorn** - ASGI server for production
- **pydantic** - Data validation and serialization
- **python-multipart** - Form data handling
- **pyodbc** or **sqlalchemy** - SQL Server connectivity

### Database Schema

#### AI_Messages Table
```sql
CREATE TABLE AI_Messages (
    Message_ID INT IDENTITY(1,1) NOT NULL,
    Posted     DATETIME NOT NULL DEFAULT GETDATE(),
    User_From  VARCHAR(15) NOT NULL,
    User_To    VARCHAR(15) NOT NULL,
    Message    VARCHAR(MAX),
    User_Read  DATETIME,
    CONSTRAINT PK_AI_Messages PRIMARY KEY (Message_ID)
);
```

#### AI_Query_History Table
```sql
CREATE TABLE AI_Query_History (
    Query_ID INT IDENTITY(1,1) NOT NULL,
    Agent VARCHAR(30) NOT NULL,
    Database_Name VARCHAR(100),
    SQL_Query VARCHAR(MAX),
    Executed_Time DATETIME NOT NULL DEFAULT GETDATE(),
    Row_Count INT,
    Execution_Time_MS INT,
    CONSTRAINT PK_AI_Query_History PRIMARY KEY (Query_ID),
    CONSTRAINT FK_AI_Query_History_Agent FOREIGN KEY (Agent) REFERENCES 
AI_Agents(Agent)
);
```

---

## MCP Tools for Database Access

### Essential Tools for AI Agents

#### Connection Management
- **connect_to_database**
  - Parameters: `server_instance`, `database_name`, `connection_string` 
(optional)
  - Returns: Connection status and database metadata

- **list_databases** 
  - Parameters: `server_instance`
  - Returns: Array of available database names

#### Schema Discovery
- **get_schema_info**
  - Parameters: `database_name`, `object_types` (optional)
  - Returns: Tables, views, stored procedures structure

- **describe_table**
  - Parameters: `database_name`, `table_name`, `include_sample_data` (optional)
  - Returns: Column definitions, constraints, relationships, sample data

- **get_table_relationships**
  - Parameters: `database_name`, `table_name` (optional)
  - Returns: Foreign key relationships

- **get_table_dependencies**
  - Parameters: `database_name`, `table_name` (optional)
  - Returns: Views and objects that depend on this table

#### Query Execution
- **execute_query**
  - Parameters: `database_name`, `sql_query`, `row_limit` (default: 1000)
  - Returns: Query results as structured data
  - **Restriction**: SELECT statements only

- **validate_sql**
  - Parameters: `database_name`, `sql_query` 
  - Returns: Syntax validation results

- **get_query_history**
  - Parameters: `agent_name`, `limit` (optional)
  - Returns: Previous queries executed by this agent for learning

- **check_permissions**
  - Parameters: `database_name`, `object_name`, `operation` 
(SELECT/INSERT/UPDATE/DELETE)
  - Returns: Whether agent has permission for the operation

#### Data Exploration
- **sample_table**
  - Parameters: `database_name`, `table_name`, `row_count`, `columns` (optional)
  - Returns: Representative sample data

- **get_column_stats**
  - Parameters: `database_name`, `table_name`, `column_name`
  - Returns: Basic statistics (nulls, unique values, min/max)

#### Agent Memory Management
- **store_memory**
  - Parameters: `agent_name`, `memory_label`, `memory_content`, 
`related_to_tags`, `purge_after` (optional)
  - Returns: Memory ID of stored memory
  - Purpose: Save information for future reference

- **retrieve_memories**
  - Parameters: `agent_name`, `related_to_tags`, `limit` (optional)
  - Returns: List of matching memories with recall count updated
  - Purpose: Find relevant memories by tags

- **search_memories**
  - Parameters: `agent_name`, `search_text`, `limit` (optional)
  - Returns: Memories containing the search text
  - Purpose: Full-text search through memory content

- **update_memory**
  - Parameters: `memory_id`, `memory_content`, `related_to_tags` (optional)
  - Returns: Success status
  - Purpose: Modify existing memory

- **delete_memory**
  - Parameters: `memory_id`
  - Returns: Success status
  - Purpose: Remove specific memory

- **get_memory_stats**
  - Parameters: `agent_name`
  - Returns: Count of memories, most used tags, etc.
  - Purpose: Memory usage overview

---

## DataLink Class

### Purpose
Centralized database access layer with error handling, connection management, 
and logging capabilities.

### Class Definition
```python
class DataLink:
    def __init__(self, instances, home_db="", debug=False):
        """
        instances example:
        [
            {
                "instance": "myserver\\myinstance",
                "user": "secret", 
                "password": "secret"
            }
        ]
        """
        self.wasError = False  # Error flag management
    
    def __del__(self):
        """Clean up connections"""
        
    def sql_escape(self, data, quote=True):
        """Escape SQL strings (replace ' with '')"""
        
    def sql_get(self, sql):
        """Execute SELECT query, return list of dictionaries"""
        
    def to_columns(self, list_of_dict):
        """Convert list of dicts to dictionary of lists"""
        
    def to_rows(self, dict_of_list):
        """Convert dictionary of lists to list of dictionaries"""
        
    def sql_run(self, sql):
        """Execute SQL statement with no return value"""
        
    def sql_insert(self, table_name, data, chunk_size=500, run=True):
        """Generate/execute INSERT statements in chunks"""
        
    def sql_upsert(self, table_name, data, key=[], run=True):
        """Update if exists, otherwise insert"""
        
    def log(self, message):
        """Save message to application log"""
        
    def read_log(self, num):
        """Return last num log entries"""
```

### Error Handling
- All database errors logged with SQL statement context
- Automatic retry logic for connection failures with exponential backoff
- Connection pooling and cleanup management

---

## Implementation Notes

### Agent Scheduling & Messaging
- Each agent polls independently on its own schedule (no coordination required)
- Users select one specific agent per message (no multi-agent messaging)
- Agents process their message queue independently without knowledge of other 
agents
- No session management - all interactions are transactional

### MCP Tool Implementation
- Memory management tools integrate with AI_Memories table
- Query history tracking for agent learning and improvement
- Permission checking to ensure database security
- All database operations go through DataLink class for consistency

### Performance Considerations
- Connection pooling for database access via DataLink class
- Query result limiting (default 1000 rows)
- Chunked data operations for large datasets
- Independent agent polling prevents conflicts and resource contention

### SQL Server 2019 Compatibility
- Uses SQL Server 2019 features and syntax
- IDENTITY columns for auto-incrementing IDs
- VARCHAR(MAX) for large text storage
- Modern constraint naming conventions
- Full-text search capabilities for memory search

---

### Configuration Enhancements
```yaml
# config.yaml
database:
  instances:
    - instance: "myserver\\myinstance"
      user: "triai_user"
      password: "secure_password"
  home_db: "TriAI_Main"

models:
  default:
    api: "ollama"
    model: "qwen2.5-coder"
  
  openai:
    api_key: "sk-..."
    model: "gpt-4"
    
  anthropic:
    api_key: "sk-ant-..."
    model: "claude-3-sonnet"

server:
  host: "0.0.0.0"
  port: 8080
  public_folder: "./public"
  reload: false  # Set to true for development
  
fastapi:
  title: "TriAI Messaging Server"
  description: "Multi-agent AI framework with database integration"
  version: "1.0.0"
  docs_url: "/docs"  # Swagger UI
  redoc_url: "/redoc"  # ReDoc documentation

user:
  current_user: "testuser"  # Hardcoded for now
```

### FastAPI Server Startup
```python
# main.py
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import yaml
from datalink import DataLink

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize DataLink for database access
db = DataLink(config["database"]["instances"], config["database"]["home_db"])

# Initialize FastAPI app
app = FastAPI(
    title=config["fastapi"]["title"],
    description=config["fastapi"]["description"], 
    version=config["fastapi"]["version"],
    docs_url=config["fastapi"]["docs_url"],
    redoc_url=config["fastapi"]["redoc_url"]
)

# Mount static files
app.mount("/", StaticFiles(directory=config["server"]["public_folder"], 
html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=config["server"]["reload"]
    )
```
