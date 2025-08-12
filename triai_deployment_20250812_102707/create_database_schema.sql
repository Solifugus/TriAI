-- TriAI Database Schema for SQL Server
-- Run this script on your SQL Server database

USE [TriAI_Main]  -- Change to your database name
GO

-- Agent registration and configuration
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Agents' AND xtype='U')
CREATE TABLE dbo.AI_Agents(
    Agent              VARCHAR(15) UNIQUE NOT NULL,
    Description        VARCHAR(100),       -- public description
    Role               VARCHAR(MAX),       -- agent's system prompt
    Model_API          VARCHAR(300),
    Model              VARCHAR(100),
    Polling_Interval   INT,
    PRIMARY KEY (Agent)
)
GO

-- Message storage between users and agents
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Messages' AND xtype='U')
CREATE TABLE dbo.AI_Messages(
    Message_ID     INT IDENTITY(1,1),
    Posted         DATETIME DEFAULT GETDATE(),
    User_From      VARCHAR(15),
    User_To        VARCHAR(15),
    Message        VARCHAR(MAX),
    User_Read      DATETIME,
    PRIMARY KEY (Message_ID)
)
GO

-- Agent memory system for persistent knowledge
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Memories' AND xtype='U')
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
GO

-- Script storage and metadata (optional)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Scripts' AND xtype='U')
CREATE TABLE dbo.AI_Scripts(
    Language       VARCHAR(15),
    Folder         VARCHAR(100),
    FileName       VARCHAR(100),
    Summary        VARCHAR(6000),
    Script         VARCHAR(MAX) NULL
)
GO

-- Insert default agents (update as needed)
IF NOT EXISTS (SELECT * FROM AI_Agents WHERE Agent = 'DataAnalyst')
INSERT INTO AI_Agents(Agent, Description, Role, Model_API, Model, Polling_Interval)
VALUES(
    'DataAnalyst',
    'Analyzes business data and generates reports',
    'You are a data analyst who proactively queries databases to answer user questions about business data, customer information, and analytics. When users ask about data, execute queries directly instead of offering to help them write queries.',
    'ollama',
    'qwen2.5-coder',
    3
)
GO

IF NOT EXISTS (SELECT * FROM AI_Agents WHERE Agent = 'QueryBot') 
INSERT INTO AI_Agents(Agent, Description, Role, Model_API, Model, Polling_Interval)
VALUES(
    'QueryBot',
    'Executes database queries and explains results',
    'You are a database query specialist who directly executes SQL queries to retrieve and analyze data for users. Always be proactive - if you can answer a question by querying data, DO IT immediately.',
    'ollama', 
    'qwen2.5-coder',
    3
)
GO

PRINT 'TriAI database schema created successfully!'
GO
