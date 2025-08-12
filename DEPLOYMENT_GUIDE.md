# TriAI Production Deployment Guide

## Overview

This guide explains how to deploy the enhanced TriAI system with proper MCP (Model Context Protocol) tools integration to your production SQL Server environment.

## What's Fixed

The previous version was **NOT using MCP tools** - agents would offer to help write queries instead of executing them directly. This deployment includes:

✅ **SQL Server MCP Tools** - Direct database query execution  
✅ **Enhanced Agent Server** - Proactive database access  
✅ **Intelligent Query Analysis** - Automatic SQL generation from natural language  
✅ **Memory System** - Persistent agent knowledge  
✅ **Multi-Database Support** - Works with Mock, PostgreSQL, and SQL Server  

## Files to Deploy

### Core System Files
```
main.py                     # FastAPI messaging server (UPDATED)
enhanced_agent_server.py    # Enhanced agent with MCP tools (NEW)
mcp_tools_sqlserver.py     # SQL Server MCP tools (NEW) 
schema_compatibility.py     # Multi-database compatibility (NEW)
config.yaml                 # Configuration file (UPDATE REQUIRED)
requirements.txt            # Python dependencies
```

### Database Integration
```
datalink.py               # SQL Server database connector
mcp_tools.py              # Generic MCP tools (fallback)
models.py                 # Data models
```

### Web Client
```
public/
├── index.html           # Web interface  
├── app.js               # JavaScript client
└── styles.css           # Styling
```

## Deployment Steps

### 1. Update Configuration

Edit your `config.yaml` for production:

```yaml
database:
  type: "sqlserver"  # Change from "mock" to "sqlserver"
  sqlserver:
    instances:
      - instance: "your-server\\your-instance"  # Your SQL Server instance
        user: "your_username"
        password: "your_password"
    home_db: "TriAI_Main"  # Your database name

server:
  use_mock_db: false  # Change from true to false
  host: "0.0.0.0"
  port: 8080

# Update agents to match your database
agents:
  - name: "DataAnalyst" 
    description: "Analyzes business data and generates reports"
    model_api: "ollama"
    model: "qwen2.5-coder"
    polling_interval: 3
  
  - name: "QueryBot"
    description: "Executes database queries and explains results"
    model_api: "ollama" 
    model: "qwen2.5-coder"
    polling_interval: 3
```

### 2. Create Database Tables

Run this SQL script on your SQL Server to create the required tables:

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

-- Script storage and metadata (optional)
CREATE TABLE dbo.AI_Scripts(
    Language       VARCHAR(15),
    Folder         VARCHAR(100),
    FileName       VARCHAR(100),
    Summary        VARCHAR(6000),
    Script         VARCHAR(MAX) NULL
)

-- Insert your agents
INSERT INTO AI_Agents(Agent, Description, Role, Model_API, Model, Polling_Interval)
VALUES
    ('DataAnalyst', 'Analyzes business data and generates reports', 
     'You are a data analyst who proactively queries databases to answer user questions about business data, customer information, and analytics.', 
     'ollama', 'qwen2.5-coder', 3),
    ('QueryBot', 'Executes database queries and explains results',
     'You are a database query specialist who directly executes SQL queries to retrieve and analyze data for users.',
     'ollama', 'qwen2.5-coder', 3)
```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn websockets pyyaml pyodbc requests
```

### 4. Start Services

#### Option A: Start Individual Services (Recommended for testing)

```bash
# Terminal 1: Start messaging server
python main.py

# Terminal 2: Start enhanced agents  
python enhanced_agent_server.py
```

#### Option B: Use Systemd Services (Production)

Create service files:

**triai-messaging.service:**
```ini
[Unit]
Description=TriAI Messaging Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/triai
ExecStart=/path/to/triai/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**triai-agents.service:**
```ini
[Unit]  
Description=TriAI Enhanced Agents
After=network.target triai-messaging.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/triai
ExecStart=/path/to/triai/venv/bin/python enhanced_agent_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable triai-messaging.service
sudo systemctl enable triai-agents.service
sudo systemctl start triai-messaging.service
sudo systemctl start triai-agents.service
```

### 5. Test the System

1. **Web Interface**: Navigate to `http://your-server:8080`

2. **Test Database Integration**: Ask an agent:
   - "How many records are in the Customer table?"  
   - "Show me the latest 5 orders"
   - "What products do we have?"

3. **Verify MCP Tools**: Agents should respond with actual data, not offers to help write queries

## Key Differences from Previous Version

### Before (Broken):
```
User: "How many customers do we have?"
Agent: "I can help you write a query like: SELECT COUNT(*) FROM Customers"
```

### After (Fixed):  
```
User: "How many customers do we have?"
Agent: "Based on our database, we currently have 1,247 active customers."
```

## Architecture Improvements

### 1. **Proactive Database Access**
- Agents analyze user questions and automatically execute appropriate queries
- No more "I can help you write a query" responses
- Direct data retrieval and analysis

### 2. **Intelligent Query Generation**  
- Natural language processing to determine user intent
- Automatic SQL generation based on available tables
- Context-aware query execution

### 3. **Enhanced Memory System**
- Agents remember previous queries and results
- Learning from user interactions
- Persistent knowledge across sessions

### 4. **Multi-Database Compatibility**
- Same codebase works with SQL Server, PostgreSQL, and Mock databases
- Automatic field name mapping and query syntax adaptation
- Easy switching between database types

## Troubleshooting

### Agents Not Executing Queries

**Problem**: Agents still offer to write queries instead of executing them

**Solution**: 
1. Ensure you're using `enhanced_agent_server.py`, not `agent_server.py`
2. Verify `use_mock_db: false` in config.yaml  
3. Check database connection in server logs

### Database Connection Issues

**Problem**: "Cannot connect to database" errors

**Solution**:
1. Verify SQL Server instance name and credentials in config.yaml
2. Ensure SQL Server allows remote connections
3. Check firewall settings for port access
4. Test connection manually: `sqlcmd -S server\\instance -U username -P password`

### Missing MCP Tools

**Problem**: Agents can't access MCP tools

**Solution**:
1. Verify `mcp_tools_sqlserver.py` is imported in `main.py`
2. Check server logs for MCP tool initialization
3. Ensure database tables (AI_Memories, etc.) exist

## Monitoring

Monitor these log messages for proper operation:

### Successful Startup
```
[2024-01-15 10:00:00] INFO - Starting enhanced agent DataAnalyst
[2024-01-15 10:00:01] INFO - Enhanced agent DataAnalyst is active with MCP database access
[2024-01-15 10:00:02] INFO - Available MCP tools: 12
```

### Successful Query Execution
```
[DataAnalyst] 2024-01-15 10:05:00 - INFO - Handling database query for: How many customers...
[DataAnalyst] 2024-01-15 10:05:01 - INFO - MCP response: True
```

## Performance Notes

- **Query Limits**: Queries are limited to 1000 rows by default for performance
- **Memory Usage**: Agents cache memories and query results
- **Polling Interval**: Default 3 seconds, adjust based on server load
- **Connection Pooling**: Database connections are pooled and reused

## Security

- **Query Restrictions**: Only SELECT statements allowed
- **SQL Injection Prevention**: All queries use parameter escaping  
- **Permission Checking**: Agents can only read data, not modify
- **Audit Trail**: All queries logged in AI_Query_History table (if created)

Your production deployment should now have agents that **actually execute database queries** instead of just offering to help write them!