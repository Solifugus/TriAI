# TriAI

This is an AI framework based on the following three components: 

- messaging server
- browser client
- agent Server


## Agent Server

One agent should wake up at a time, taking turns, to check its messages and 
respond to them.  They may use the MCP library available.

Options for models to use should be on:

- Ollama locally
- O365 CoPilot API
- OpenAI
- Athropic API

By default, we will use Ollama locally, the qwen2.5-coder model.  The model 
name and API keys, where relevant, should be kept in a config.yaml file.
The database connection string parameters should also be kept there.


Each agent is registered in the following table:

CREATE TABLE AI_Agents (
    Agent       VARCHAR(15) UNIQUE,
    Description VARCHAR(MAX),
    Model_API   VARCHAR(30),
    Model       VARCHAR(100),
    Model_API_KEY VARCHAR(500)
    PRIMARY KEY( Agent )
)

Agent memories (notes to remember across sessions) should be stored in:

CREATE TABLE AI_Memories (
    Memory_ID    INT UNIQUE IDENTITY(1,1),
    Agent        VARCHAR(15),
    First_Posted DATETIME DEFAULT GETDATE(),
    Times_Recalled INT DEFAULT 0,
    Last_Recalled  DATETIME,
    Memory_Label   VARCHAR(100) NOT NULL,
    Memory         VARCHAR(MAX),
    Related_To     VARCHAR(200) NOT NULL,
    Purge_After    DATETIME,
    PRIMARY KEY( Memory_ID )
)

The Related_To column is a list of space separated tags to group things by key 
terms.  

## Browser Client

The Browser Client should provide a large chat windows.  It should have a blue 
theme and be based purely on HTML. CSS, and Javascript -- vanilla.  The user 
should be able to choose the agent he/she wishes to message with.

It should also be able to show tabular query results, when applicable.
A REST call should be used to the server to get the user's name.

## Messaging Server

- Servers web files in a /public folder over HTTP.
- Mediates messages between users/agents via REST.
- Servers tool access to agents using MCP (Model Context Protocol).

Messages should be stored in the table:

CREATE TABLE AI_Messages (
    Message_ID    INT UNIQUE IDENTITY(1,1),
    Posted        DATETIME,
    User_From     VARCHAR(15),
    User_To       VARCHAR(15),
    Message       VARCHAR(MAX),
    User_Read     DATETIME,
    PRIMARY KEY( Message_ID )
)

The users could be the user's name or the an AI agent's name. 
### MCP Calls

This document outlines the Model Context Protocol (MCP) calls needed for AI 
agents to access and work with SQL Server databases, including instances like 
`myserver\myinstance`.

TODO

### DataLink class

This class should be used for all database access.
If an error occurs, the error should be logged along with the SQL statement
that errored.  If the database connection is lost, it should log
the event, pause a while, and retry -- repeatedly.

class DataLink:

    def __init__(self, instances, home_db = "", debug=False):
        """ instances example:
        [
            {
                "insance":"myserver\myinstance",
                "user":"secret",
                "password":"secret"
            },
            ..
        ]
        """
        self.wasError = False  # set True upon error then False on next call

    def __del__(self):
        # clean up

    def sql_escape( self, data, quote=True ):
        # returns data with any ' escaped with ''

    def sql_get( self, sql ):
        # returns list of dictionaries from a given select query

    def to_columns( self, list_of_dict ):
        # returns converted to dictionary of lists

    def to_rows( self, dict_of_list ):
        # returns converted to list of dictionaries

    def sql_run( self, sql ):
        # executes SQL statement with no return value

    def sql_insert( self, table_name, data, chunk_size=500, run=True ):
        # converts data to SQL insert statements in chunks.
        # data may be list of dictionaries or dictionary of lists
        # if run = False, returns SQL else runs it.

    def sql_upsert( self, data, key=[], run=True ):
        # to update if exists else insert
        # data may be list of dictionaries or dictionary of lists
        # if run = False, returns SQL else runs it.

    def log( self, message ):
        # save to log

    def read_log( self, num ):
        # return last num entries in log
