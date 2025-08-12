# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TriAI is a multi-agent AI framework consisting of three core components:

- **Messaging Server** (Python FastAPI) - Central hub for communication and MCP tool serving
- **Browser Client** (HTML/CSS/JavaScript) - Web-based user interface for agent interaction  
- **Agent Server** - AI agents that process messages and execute tasks

## Architecture

### Agent System
- Agents operate independently on turn-based polling cycles
- Each agent connects via WebSocket to `/ws/agent/{agent_name}`
- Agents use MCP (Model Context Protocol) tools for database access
- No broadcasting - users message one specific agent at a time
- Agent configuration stored in `AI_Agents` table with model API settings

### Database Schema
The framework supports three data storage options:
- **Mock Database** - In-memory data structures for testing and development
- **SQL Server 2019** - Production deployment option
- **PostgreSQL** - Alternative production deployment option

The same schema is implemented across all three options:

#### SQL Server Schema

```sql
-- Agent registration and configuration
CREATE TABLE dbo.AI_Agents(
    Agent              VARCHAR(15) UNIQUE NOT NULL,
    Description        VARCHAR(100),       -- public description
    Role               VARCHAR(MAX),       -- agent's reference
    Model_API          VARCHAR(300),
    Model              VARCHAR(100),
    Polling_Interval   INT,
    PRIMARY KEY (Agent)
)

-- Message storage between users and agents
CREATE TABLE dbo.AI_Messages(
    Message_ID     INT IDENTITY(1,1),
    Posted         DATETIME DEFAULT GETDATE(),
    User_From      VARCHAR(15),
    User_To        VARCHAR(15),
    Message        VARCHAR(MAX),
    User_Read      DATETIME,
    PRIMARY KEY (Message_ID)
)

-- Agent memory system for persistent knowledge
CREATE TABLE dbo.AI_Memories(
    Memory_ID      INT IDENTITY(1,1),
    Agent          VARCHAR(15),
    First_Posted   DATETIME DEFAULT GETDATE(),
    Times_Recalled INT DEFAULT 0,
    Last_Recalled  DATETIME,
    Memory_label   VARCHAR(100),
    Memory         VARCHAR(MAX),
    Related_To     VARCHAR(100),
    Purge_After    DATETIME,
    PRIMARY KEY (Memory_ID)
)

-- Script storage and metadata
CREATE TABLE dbo.AI_Scripts(
    Language       VARCHAR(15),
    Folder         VARCHAR(100),
    FileName       VARCHAR(100),
    Summary        VARCHAR(6000),
    Script         VARCHAR(MAX) NULL
)
```

#### PostgreSQL Schema

```sql
-- Agent registration and configuration
CREATE TABLE AI_Agents(
    Agent              VARCHAR(15) UNIQUE NOT NULL,
    Description        VARCHAR(100),       -- public description
    Role               TEXT,               -- agent's reference
    Model_API          VARCHAR(300),
    Model              VARCHAR(100),
    Polling_Interval   INTEGER,
    PRIMARY KEY (Agent)
);

-- Message storage between users and agents
CREATE TABLE AI_Messages(
    Message_ID     SERIAL PRIMARY KEY,
    Posted         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    User_From      VARCHAR(15),
    User_To        VARCHAR(15),
    Message        TEXT,
    User_Read      TIMESTAMP
);

-- Agent memory system for persistent knowledge
CREATE TABLE AI_Memories(
    Memory_ID      SERIAL PRIMARY KEY,
    Agent          VARCHAR(15),
    First_Posted   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Times_Recalled INTEGER DEFAULT 0,
    Last_Recalled  TIMESTAMP,
    Memory_label   VARCHAR(100),
    Memory         TEXT,
    Related_To     VARCHAR(100),
    Purge_After    TIMESTAMP
);

-- Script storage and metadata
CREATE TABLE AI_Scripts(
    Language       VARCHAR(15),
    Folder         VARCHAR(100),
    FileName       VARCHAR(100),
    Summary        VARCHAR(6000),
    Script         TEXT
);
```

### DataLink Class
All database operations must go through the `DataLink` class which provides a unified interface across all three storage options:
- **Mock Mode** - Uses in-memory dictionaries and lists for testing
- **SQL Server** - Uses pyodbc with connection pooling and retry logic  
- **PostgreSQL** - Uses psycopg2 with connection pooling and retry logic

Core functionality:
- Database abstraction layer with consistent API
- SQL injection prevention via `sql_escape()` 
- Error logging with SQL context
- Data format conversion between lists/dictionaries
- Chunked operations for large datasets

Key methods:
- `sql_get(sql)` - Execute SELECT queries, returns list of dictionaries
- `sql_run(sql)` - Execute statements with no return value
- `sql_insert(table_name, data, chunk_size=500)` - Bulk insert operations
- `sql_upsert(table_name, data, key=[])` - Update or insert operations

Database selection is controlled via `config.yaml` with the `database_type` setting (`mock`, `sqlserver`, or `postgresql`).

## Development Commands

Since this is a design-phase repository with only documentation files, there are no build, test, or lint commands defined yet. The implementation will use:

- **FastAPI** for the messaging server with uvicorn
- **Python** for agent servers and MCP tools
- **Vanilla HTML/CSS/JavaScript** for the browser client
- **Multi-database support** for data persistence (Mock/SQL Server 2019/PostgreSQL)

## Model Support

The framework supports multiple AI providers:
- **Ollama** (local, default: qwen2.5-coder model)
- **Microsoft 365 Copilot API**
- **OpenAI API** 
- **Anthropic API**

Configuration managed through `config.yaml` containing model settings, API keys, and database connection parameters.

## MCP Tools for Agents

Essential tools provided via WebSocket:

### Database Access
- `connect_to_database`, `list_databases` - Connection management
- `get_schema_info`, `describe_table` - Schema discovery  
- `execute_query` (SELECT only), `validate_sql` - Query execution
- `sample_table`, `get_column_stats` - Data exploration

### Memory Management
- `store_memory`, `retrieve_memories` - Persistent agent knowledge
- `search_memories`, `update_memory`, `delete_memory` - Memory operations
- Uses `Related_To` field with space-separated tags for categorization

### Query History
- `get_query_history` - Previous queries for agent learning
- `check_permissions` - Database security validation

## Key Design Principles

- **Independent Agent Operation** - No coordination required between agents
- **Transactional Messaging** - No session state maintenance
- **Database-Agnostic Architecture** - Unified data layer supporting Mock/SQL Server/PostgreSQL
- **Security Focus** - SELECT-only queries, permission checking, SQL injection prevention  
- **Performance Considerations** - Connection pooling, query result limits (1000 rows default), chunked operations