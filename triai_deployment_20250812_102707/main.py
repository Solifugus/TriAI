"""
TriAI FastAPI Messaging Server
Multi-agent AI framework with database integration and MCP tool support.
"""

import os
import yaml
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Import our modules
from models import (
    MessageRequest, MessageResponse, AgentInfo, MCPRequest, MCPResponse,
    MemoryRequest, MemoryResponse, QueryHistoryResponse
)
try:
    from datalink import DataLink
    DATALINK_AVAILABLE = True
except ImportError:
    DataLink = None
    DATALINK_AVAILABLE = False

try:
    from pg_datalink import PostgreSQLDataLink
    POSTGRESQL_AVAILABLE = True
except ImportError:
    PostgreSQLDataLink = None
    POSTGRESQL_AVAILABLE = False
    
from mock_datalink import MockDataLink
from mcp_tools import MCPToolProvider
from mcp_tools_pg import PostgreSQLMCPToolProvider
from mcp_tools_sqlserver import SQLServerMCPToolProvider


class TriAIServer:
    """Main TriAI messaging server class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the TriAI server."""
        self.config = self._load_config(config_path)
        self.app = self._create_fastapi_app()
        self.db = self._initialize_database()
        self.mcp_tools = self._initialize_mcp_tools()
        self.connected_agents: Dict[str, WebSocket] = {}
        
        # Setup routes
        self._setup_rest_routes()
        self._setup_websocket_routes() 
        self._setup_static_files()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration if file not found
            return {
                "database": {"instances": [], "home_db": ""},
                "server": {"host": "0.0.0.0", "port": 8080, "use_mock_db": True},
                "fastapi": {"title": "TriAI Server", "version": "1.0.0"},
                "user": {"current_user": "testuser"}
            }
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        return FastAPI(
            title=self.config["fastapi"]["title"],
            description=self.config["fastapi"]["description"],
            version=self.config["fastapi"]["version"],
            docs_url=self.config["fastapi"].get("docs_url", "/docs"),
            redoc_url=self.config["fastapi"].get("redoc_url", "/redoc")
        )
    
    def _initialize_database(self) -> Any:
        """Initialize database connection."""
        if self.config["server"].get("use_mock_db", True):
            # Use mock database
            instances = self.config["database"].get("sqlserver", {}).get("instances", [])
            home_db = self.config["database"].get("sqlserver", {}).get("home_db", "")
            return MockDataLink(instances, home_db, debug=True)
        
        # Use real database based on type
        db_type = self.config["database"].get("type", "mock")
        
        if db_type == "postgresql" and POSTGRESQL_AVAILABLE:
            pg_config = self.config["database"]["postgresql"]
            return PostgreSQLDataLink(pg_config, debug=True)
        
        elif db_type == "sqlserver" and DATALINK_AVAILABLE:
            sql_config = self.config["database"]["sqlserver"]
            return DataLink(
                sql_config["instances"],
                sql_config["home_db"],
                debug=True
            )
        
        else:
            # Fallback to mock
            print(f"⚠️ Database type '{db_type}' not available, using mock database")
            instances = self.config["database"].get("sqlserver", {}).get("instances", [])
            home_db = self.config["database"].get("sqlserver", {}).get("home_db", "")
            return MockDataLink(instances, home_db, debug=True)
    
    def _initialize_mcp_tools(self):
        """Initialize MCP tools based on database type."""
        if self.config["server"].get("use_mock_db", True):
            # Use generic MCP tools for mock database
            return MCPToolProvider(self.db)
        
        # Use database-specific MCP tools based on type
        db_type = self.config["database"].get("type", "mock")
        
        if db_type == "postgresql" and POSTGRESQL_AVAILABLE:
            return PostgreSQLMCPToolProvider(self.db)
        elif db_type == "sqlserver" and DATALINK_AVAILABLE:
            return SQLServerMCPToolProvider(self.db)
        else:
            # Fallback to generic MCP tools
            return MCPToolProvider(self.db)
    
    def _setup_rest_routes(self):
        """Setup REST API routes."""
        
        @self.app.get("/api/user")
        async def get_current_user() -> Dict[str, str]:
            """Returns current user identification."""
            return {"username": self.config["user"]["current_user"]}
        
        @self.app.get("/api/config")
        async def get_app_config() -> Dict[str, Any]:
            """Returns application configuration for UI."""
            return {
                "application": self.config.get("application", {
                    "name": "TriAI",
                    "display_name": "TriAI Analytics Platform",
                    "description": "Multi-agent AI framework with database integration"
                })
            }
        
        @self.app.get("/api/agents", response_model=List[AgentInfo])
        async def get_agents() -> List[AgentInfo]:
            """Returns available agents with descriptions from AI_Agents table."""
            try:
                agents_data = self.db.sql_get("SELECT Agent, Description, Model_API, Model FROM AI_Agents")
                return [
                    AgentInfo(
                        agent=agent.get("Agent") or agent.get("agent"),
                        description=agent.get("Description") or agent.get("description") or "No description",
                        model_api=agent.get("Model_API") or agent.get("model_api") or "unknown",
                        model=agent.get("Model") or agent.get("model") or "unknown"
                    )
                    for agent in agents_data
                ]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch agents: {str(e)}")
        
        @self.app.post("/api/message")
        async def send_message(message: MessageRequest) -> Dict[str, Any]:
            """Accept user messages for specific agents."""
            try:
                # Store message in database
                message_data = [{
                    "posted": datetime.now(),
                    "user_from": self.config["user"]["current_user"],
                    "user_to": message.user_to,
                    "message": message.message,
                    "user_read": None
                }]
                
                self.db.sql_insert("AI_Messages", message_data)
                
                # Notify agent via WebSocket if connected
                if message.user_to in self.connected_agents:
                    websocket = self.connected_agents[message.user_to]
                    try:
                        await websocket.send_json({
                            "type": "new_message",
                            "from": self.config["user"]["current_user"],
                            "message": message.message,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        self.db.log(f"Failed to notify agent {message.user_to}: {str(e)}")
                
                return {
                    "success": True,
                    "message": "Message sent successfully",
                    "recipient": message.user_to
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
        
        @self.app.get("/api/messages/{agent}", response_model=List[MessageResponse])
        async def get_messages(agent: str, limit: int = 50) -> List[MessageResponse]:
            """Returns conversation history with specific agent."""
            try:
                query = f"""
                SELECT message_id, posted, user_from, user_to, message, user_read
                FROM AI_Messages 
                WHERE (user_from = '{agent}' AND user_to = '{self.config["user"]["current_user"]}')
                   OR (user_from = '{self.config["user"]["current_user"]}' AND user_to = '{agent}')
                ORDER BY posted DESC
                LIMIT {limit}
                """
                
                messages_data = self.db.sql_get(query)
                
                return [
                    MessageResponse(
                        message_id=msg.get("Message_ID") or msg.get("message_id"),
                        posted=msg.get("Posted") or msg.get("posted"),
                        user_from=msg.get("User_From") or msg.get("user_from"),
                        user_to=msg.get("User_To") or msg.get("user_to"),
                        message=msg.get("Message") or msg.get("message"),
                        user_read=msg.get("User_Read") or msg.get("user_read")
                    )
                    for msg in messages_data
                ]
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")
        
        @self.app.get("/api/agents/{agent_name}/memories")
        async def get_agent_memories(agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
            """Get memories for a specific agent."""
            try:
                query = f"""
                SELECT memory_id, agent, first_posted, times_recalled, last_recalled,
                       memory_label, memory, related_to, purge_after
                FROM AI_Memories 
                WHERE agent = '{agent_name}'
                ORDER BY last_recalled DESC, first_posted DESC
                LIMIT {limit}
                """
                
                return self.db.sql_get(query)
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch memories: {str(e)}")
        
        @self.app.get("/api/agents/{agent_name}/query-history")
        async def get_agent_query_history(agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
            """Get query history for a specific agent."""
            try:
                result = self.mcp_tools.get_query_history(agent_name, limit)
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch query history: {str(e)}")
    
    def _setup_websocket_routes(self):
        """Setup WebSocket routes for agent connections."""
        
        @self.app.websocket("/ws/agent/{agent_name}")
        async def agent_websocket(websocket: WebSocket, agent_name: str):
            """WebSocket endpoint for agent connections and MCP tool access."""
            await websocket.accept()
            
            # Verify agent exists in database
            try:
                agents = self.db.sql_get(f"SELECT agent FROM AI_Agents WHERE agent = '{agent_name}'")
                if not agents:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Agent '{agent_name}' not found in database"
                    })
                    await websocket.close()
                    return
            except Exception as e:
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Database error: {str(e)}"
                })
                await websocket.close()
                return
            
            # Register agent connection
            self.connected_agents[agent_name] = websocket
            self.db.log(f"Agent {agent_name} connected via WebSocket")
            
            try:
                # Send connection confirmation
                await websocket.send_json({
                    "type": "connected",
                    "agent_name": agent_name,
                    "server_time": datetime.now().isoformat(),
                    "available_tools": list(self.mcp_tools.tools.keys())
                })
                
                # Message handling loop
                while True:
                    try:
                        data = await websocket.receive_json()
                        
                        if data.get("type") == "mcp_request":
                            # Handle MCP tool request
                            tool_name = data.get("tool")
                            parameters = data.get("parameters", {})
                            
                            if not tool_name:
                                await websocket.send_json({
                                    "type": "mcp_response",
                                    "success": False,
                                    "error": "Missing tool name"
                                })
                                continue
                            
                            # Execute MCP tool 
                            result = self.mcp_tools.execute_tool(tool_name, parameters)
                            
                            await websocket.send_json({
                                "type": "mcp_response",
                                "tool": tool_name,
                                **result
                            })
                            
                        elif data.get("type") == "check_messages":
                            # Check for new messages for this agent
                            query = f"""
                            SELECT message_id, posted, user_from, message
                            FROM AI_Messages 
                            WHERE user_to = '{agent_name}' AND user_read IS NULL
                            ORDER BY posted ASC
                            """
                            
                            unread_messages = self.db.sql_get(query)
                            
                            await websocket.send_json({
                                "type": "messages_response",
                                "unread_count": len(unread_messages),
                                "messages": unread_messages
                            })
                            
                        elif data.get("type") == "mark_read":
                            # Mark messages as read
                            message_ids = data.get("message_ids", [])
                            
                            for msg_id in message_ids:
                                update_query = f"""
                                UPDATE AI_Messages 
                                SET user_read = CURRENT_TIMESTAMP
                                WHERE message_id = {msg_id}
                                """
                                self.db.sql_run(update_query)
                            
                            await websocket.send_json({
                                "type": "mark_read_response",
                                "success": True,
                                "marked_count": len(message_ids)
                            })
                            
                        elif data.get("type") == "send_response":
                            # Agent sending response message
                            response_msg = data.get("message", "")
                            to_user = data.get("to_user", self.config["user"]["current_user"])
                            
                            message_data = [{
                                "posted": datetime.now(),
                                "user_from": agent_name,
                                "user_to": to_user,
                                "message": response_msg,
                                "user_read": None
                            }]
                            
                            self.db.sql_insert("AI_Messages", message_data)
                            
                            await websocket.send_json({
                                "type": "send_response_ack",
                                "success": True
                            })
                            
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Unknown message type: {data.get('type')}"
                            })
                            
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid JSON format"
                        })
                        
            except WebSocketDisconnect:
                self.db.log(f"Agent {agent_name} disconnected")
            except Exception as e:
                self.db.log(f"WebSocket error for agent {agent_name}: {str(e)}")
            finally:
                # Clean up connection
                if agent_name in self.connected_agents:
                    del self.connected_agents[agent_name]
    
    def _setup_static_files(self):
        """Setup static file serving for browser client."""
        public_folder = self.config["server"].get("public_folder", "./public")
        
        # Create public folder if it doesn't exist
        os.makedirs(public_folder, exist_ok=True)
        
        # Create a simple index.html if it doesn't exist
        index_path = os.path.join(public_folder, "index.html")
        if not os.path.exists(index_path):
            app_name = self.config.get("application", {}).get("display_name", "TriAI")
            app_description = self.config.get("application", {}).get("description", "Multi-agent AI framework")
            with open(index_path, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{app_name} - Messaging Interface</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f0f8ff; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #2c5aa0; text-align: center; }}
        .status {{ padding: 10px; background: #e7f3ff; border-radius: 5px; margin-bottom: 20px; }}
        .api-links {{ background: white; padding: 20px; border-radius: 5px; }}
        .api-links a {{ display: block; margin: 10px 0; color: #2c5aa0; text-decoration: none; }}
        .api-links a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app_name}</h1>
        <div class="status">
            <h3>Server Status: Running</h3>
            <p>{app_description} - The messaging server is operational and ready to accept connections.</p>
        </div>
        <div class="api-links">
            <h3>API Documentation</h3>
            <a href="/docs">Swagger UI Documentation</a>
            <a href="/redoc">ReDoc Documentation</a>
            <h3>API Endpoints</h3>
            <a href="/api/user">Current User</a>
            <a href="/api/agents">Available Agents</a>
        </div>
    </div>
</body>
</html>""")
        
        # Mount static files
        self.app.mount("/", StaticFiles(directory=public_folder, html=True), name="static")
    
    def run(self):
        """Run the server."""
        uvicorn.run(
            self.app,
            host=self.config["server"]["host"],
            port=self.config["server"]["port"],
            reload=self.config["server"].get("reload", False),
            ws_ping_interval=20,  # Send ping every 20 seconds
            ws_ping_timeout=60,   # Wait 60 seconds for pong
            timeout_keep_alive=65  # Keep connections alive longer
        )


# Create global server instance
server = TriAIServer()
app = server.app

if __name__ == "__main__":
    server.run()