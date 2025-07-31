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
The framework uses SQL Server 2019 with these key tables:

```sql
-- Agent registration and configuration
AI_Agents (Agent, Description, Model_API, Model, Model_API_KEY)

-- Message storage between users and agents
AI_Messages (Message_ID, Posted, User_From, User_To, Message, User_Read)

-- Agent memory system for persistent knowledge
AI_Memories (Memory_ID, Agent, First_Posted, Times_Recalled, Last_Recalled, Memory_Label, Memory, Related_To, Purge_After)

-- Query execution tracking
AI_Query_History (Query_ID, Agent, Database_Name, SQL_Query, Executed_Time, Row_Count, Execution_Time_MS)
```

### DataLink Class
All database operations must go through the `DataLink` class for:
- Connection management with retry logic
- SQL injection prevention via `sql_escape()` 
- Error logging with SQL context
- Data format conversion between lists/dictionaries
- Chunked operations for large datasets

Key methods:
- `sql_get(sql)` - Execute SELECT queries, returns list of dictionaries
- `sql_run(sql)` - Execute statements with no return value
- `sql_insert(table_name, data, chunk_size=500)` - Bulk insert operations
- `sql_upsert(table_name, data, key=[])` - Update or insert operations

## Development Commands

Since this is a design-phase repository with only documentation files, there are no build, test, or lint commands defined yet. The implementation will use:

- **FastAPI** for the messaging server with uvicorn
- **Python** for agent servers and MCP tools
- **Vanilla HTML/CSS/JavaScript** for the browser client
- **SQL Server 2019** for data persistence

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
- **Database-First Architecture** - All data persisted in SQL Server
- **Security Focus** - SELECT-only queries, permission checking, SQL injection prevention  
- **Performance Considerations** - Connection pooling, query result limits (1000 rows default), chunked operations