"""
TriAI Agent Server
Implements AI agents that connect to the messaging server and process user messages.
"""

import asyncio
import json
import time
import yaml
import logging
import websockets
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import signal
import sys


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    description: str
    model_api: str
    model: str
    api_key: Optional[str] = None
    polling_interval: int = 3  # seconds
    max_retries: int = 3
    

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        
    async def generate(self, model: str, prompt: str, system_prompt: str = None) -> str:
        """Generate response using Ollama."""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "Sorry, I couldn't generate a response.")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama API error: {e}")
            return f"Error: Unable to connect to Ollama API - {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error in Ollama client: {e}")
            return f"Error: {str(e)}"
    
    def test_connection(self) -> bool:
        """Test if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class TriAIAgent:
    """
    AI Agent that connects to the messaging server and processes messages.
    """
    
    def __init__(self, config: AgentConfig, server_url: str = "ws://localhost:8080"):
        self.config = config
        self.server_url = server_url
        self.websocket = None
        self.running = False
        self.ollama = OllamaClient()
        self.mcp_tools = {}
        self.memory_cache = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format=f'[{config.name}] %(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"Agent-{config.name}")
        
        # System prompt for the agent
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """Create system prompt based on agent configuration."""
        base_prompt = f"""You are {self.config.name}, an AI assistant with the following role: {self.config.description}

Key capabilities:
- You can access databases using MCP tools to run SELECT queries and analyze data
- You can store and retrieve memories to remember important information across conversations
- You can help users with data analysis, report generation, and database queries
- You communicate clearly and provide helpful, accurate responses

Important guidelines:
- Always be helpful, accurate, and professional
- If you need to query a database, use the available MCP tools
- Store important information in memories for future reference
- If you encounter errors, explain them clearly to the user
- Keep responses concise but informative

Available MCP Tools:
- execute_query: Run SELECT queries on databases
- list_databases: See available databases
- describe_table: Get table structure information
- store_memory: Save important information
- retrieve_memories: Get relevant past memories
- get_schema_info: Understand database structure

Remember: You are having a conversation with a user. Be conversational and helpful!"""

        return base_prompt
        
    async def connect_to_server(self) -> bool:
        """Connect to the messaging server via WebSocket."""
        try:
            ws_url = f"{self.server_url}/ws/agent/{self.config.name}"
            self.logger.info(f"Connecting to messaging server: {ws_url}")
            
            self.websocket = await websockets.connect(ws_url)
            
            # Wait for connection confirmation
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            data = json.loads(response)
            
            if data.get("type") == "connected":
                self.logger.info("Successfully connected to messaging server")
                self.mcp_tools = data.get("available_tools", [])
                self.logger.info(f"Available MCP tools: {len(self.mcp_tools)}")
                return True
            else:
                self.logger.error(f"Connection failed: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to messaging server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the messaging server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.logger.info("Disconnected from messaging server")
    
    async def send_mcp_request(self, tool: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send MCP tool request to the messaging server."""
        try:
            request = {
                "type": "mcp_request",
                "tool": tool,
                "parameters": parameters
            }
            
            await self.websocket.send(json.dumps(request))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=30)
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.error(f"MCP request failed for {tool}: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_for_messages(self) -> List[Dict[str, Any]]:
        """Check for new messages from users."""
        try:
            request = {"type": "check_messages"}
            await self.websocket.send(json.dumps(request))
            
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            data = json.loads(response)
            
            if data.get("type") == "messages_response":
                return data.get("messages", [])
            elif data.get("type") == "new_message":
                # Handle real-time message notification
                self.logger.info(f"Received real-time message from {data.get('from')}: {data.get('message')}")
                # Convert to message format and return
                message = {
                    "User_From": data.get("from"),
                    "Message": data.get("message"),
                    "Message_ID": None,  # Will be set when we fetch full message
                    "Posted": data.get("timestamp")
                }
                return [message]
            elif data.get("type") in ["send_response_ack", "mcp_response"]:
                # These are expected acknowledgments/responses, not errors
                self.logger.debug(f"Received {data.get('type')} acknowledgment")
                return []
            else:
                self.logger.warning(f"Unexpected response to message check: {data}")
                return []
                
        except asyncio.TimeoutError:
            self.logger.error("Failed to check messages: Timeout waiting for server response")
            return []
        except Exception as e:
            self.logger.error(f"Failed to check messages: {type(e).__name__}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return []
    
    async def mark_messages_read(self, message_ids: List[int]):
        """Mark messages as read."""
        try:
            request = {
                "type": "mark_read",
                "message_ids": message_ids
            }
            await self.websocket.send(json.dumps(request))
            
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            data = json.loads(response)
            
            if not data.get("success"):
                self.logger.warning("Failed to mark messages as read")
                
        except Exception as e:
            self.logger.error(f"Failed to mark messages as read: {e}")
    
    async def send_response(self, message: str, to_user: str):
        """Send response message to user."""
        try:
            request = {
                "type": "send_response",
                "message": message,
                "to_user": to_user
            }
            await self.websocket.send(json.dumps(request))
            
            # Wait for acknowledgment, but handle multiple message types
            max_attempts = 3
            for attempt in range(max_attempts):
                response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("success") or data.get("type") == "send_response_ack":
                    self.logger.info(f"Response sent to {to_user}")
                    return
                elif data.get("type") in ["messages_response", "mcp_response"]:
                    # These are normal polling responses, not related to our send_response
                    self.logger.debug(f"Received unrelated message while waiting for send_response_ack: {data.get('type')}")
                    continue
                else:
                    self.logger.error(f"Failed to send response: {data}")
                    return
            
            # If we didn't get an ack after max_attempts, assume it worked
            self.logger.warning(f"No explicit acknowledgment received for response to {to_user}, but assuming success")
                
        except asyncio.TimeoutError:
            self.logger.error("Failed to send response: Timeout waiting for server acknowledgment")
        except Exception as e:
            self.logger.error(f"Failed to send response: {type(e).__name__}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    async def process_message(self, message: Dict[str, Any]) -> str:
        """Process a user message and generate AI response."""
        try:
            user_message = message.get("Message", "")
            user_from = message.get("User_From", "user")
            
            self.logger.info(f"Processing message from {user_from}: {user_message[:100]}...")
            
            # Retrieve relevant memories
            memories = await self.get_relevant_memories(user_message)
            memory_context = self._format_memories_for_context(memories)
            
            # Build context for the AI
            full_prompt = self._build_prompt_with_context(user_message, memory_context)
            
            # Generate response using Ollama
            ai_response = await self.ollama.generate(
                model=self.config.model,
                prompt=full_prompt,
                system_prompt=self.system_prompt
            )
            
            # Check if the AI wants to use MCP tools
            if self._should_use_mcp_tools(ai_response, user_message):
                ai_response = await self._handle_mcp_tool_usage(ai_response, user_message)
            
            # Store important information in memory if needed
            await self._maybe_store_memory(user_message, ai_response, user_from)
            
            return ai_response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"I apologize, but I encountered an error while processing your message: {str(e)}"
    
    def _build_prompt_with_context(self, user_message: str, memory_context: str) -> str:
        """Build prompt with memory context."""
        prompt = f"User message: {user_message}\n\n"
        
        if memory_context:
            prompt += f"Relevant memories from past conversations:\n{memory_context}\n\n"
        
        prompt += "Please provide a helpful response. If you need to query databases or access specific information, let me know and I can use the available MCP tools."
        
        return prompt
    
    def _format_memories_for_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for inclusion in prompt context."""
        if not memories:
            return ""
        
        context_parts = []
        for memory in memories[:3]:  # Use top 3 most relevant memories
            label = memory.get("Memory_Label", "Memory")
            content = memory.get("Memory", "")
            context_parts.append(f"- {label}: {content}")
        
        return "\n".join(context_parts)
    
    def _should_use_mcp_tools(self, ai_response: str, user_message: str) -> bool:
        """Determine if MCP tools should be used based on the response and user message."""
        # Simple heuristics to detect when tools might be needed
        tool_indicators = [
            "query", "database", "data", "table", "select", "sql",
            "analyze", "report", "information", "search", "find"
        ]
        
        message_lower = user_message.lower()
        response_lower = ai_response.lower()
        
        # Check if user is asking for data-related operations
        return any(indicator in message_lower for indicator in tool_indicators)
    
    async def _handle_mcp_tool_usage(self, ai_response: str, user_message: str) -> str:
        """Handle MCP tool usage for data queries."""
        try:
            message_lower = user_message.lower()
            query_executed = False
            
            # Credit Union specific queries
            if any(keyword in message_lower for keyword in ["account", "share", "member", "loan", "transaction"]):
                sql_query = None
                
                if "share" in message_lower and "account" in message_lower:
                    sql_query = "SELECT Account_Type, COUNT(*) as Count, AVG(Balance) as Average_Balance FROM Accounts WHERE Account_Type IN ('SAVINGS', 'CHECKING', 'MONEY_MARKET', 'CD') GROUP BY Account_Type"
                elif "loan" in message_lower and ("type" in message_lower or "kind" in message_lower):
                    sql_query = "SELECT Loan_Type, COUNT(*) as Count, AVG(Loan_Amount) as Avg_Amount, AVG(Interest_Rate) as Avg_Rate FROM Loans GROUP BY Loan_Type"
                elif "member" in message_lower and ("account" in message_lower or "info" in message_lower):
                    sql_query = "SELECT COUNT(*) as Total_Members, AVG(Credit_Score) as Avg_Credit_Score, COUNT(DISTINCT Branch_ID) as Branch_Count FROM Members WHERE Status = 'ACTIVE'"
                elif "transaction" in message_lower:
                    sql_query = "SELECT Transaction_Type, COUNT(*) as Count, AVG(ABS(Amount)) as Avg_Amount FROM Transactions WHERE Transaction_Date >= DATEADD(day, -30, GETDATE()) GROUP BY Transaction_Type"
                
                if sql_query:
                    query_result = await self.send_mcp_request("execute_query", {
                        "database_name": "TriAI_Main", 
                        "sql_query": sql_query
                    })
                    
                    if query_result.get("success"):
                        data = query_result.get("data", [])
                        if data:
                            query_executed = True
                            data_summary = self._format_query_results(data)
                            enhanced_response = f"{ai_response}\n\nBased on our database, here's what I found:\n{data_summary}"
                            return enhanced_response
            
            # General data queries
            if not query_executed and any(keyword in message_lower for keyword in ["data", "information", "report", "analyze"]):
                # Get available tables first
                schema_result = await self.send_mcp_request("get_schema_info", {
                    "database_name": "TriAI_Main"
                })
                
                if schema_result.get("success"):
                    # Suggest what data we have available
                    enhanced_response = f"{ai_response}\n\nI have access to our credit union database with information about:\n- Member accounts (savings, checking, CDs, money market)\n- Loans (auto, personal, mortgage, home equity)\n- Transactions and member activity\n- Branch performance metrics\n\nWhat specific information would you like me to analyze?"
                    return enhanced_response
                
            return ai_response
            
        except Exception as e:
            self.logger.error(f"Error handling MCP tools: {e}")
            return f"{ai_response}\n\n(Note: I tried to fetch additional data but encountered an error: {str(e)})"
    
    def _format_query_results(self, data: List[Dict[str, Any]]) -> str:
        """Format query results for display."""
        if not data:
            return "No data found."
        
        result = ""
        for i, row in enumerate(data):
            if i > 0:
                result += "\n"
            for key, value in row.items():
                if isinstance(value, float):
                    if key.lower().find('balance') >= 0 or key.lower().find('amount') >= 0:
                        result += f"• {key}: ${value:,.2f}\n"
                    elif key.lower().find('rate') >= 0:
                        result += f"• {key}: {value:.2f}%\n" 
                    else:
                        result += f"• {key}: {value:.2f}\n"
                elif isinstance(value, int):
                    result += f"• {key}: {value:,}\n"
                else:
                    result += f"• {key}: {value}\n"
            result += "\n"
        
        return result.strip()
    
    async def get_relevant_memories(self, user_message: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on user message."""
        try:
            # Extract key terms from user message for memory search
            search_terms = self._extract_search_terms(user_message)
            
            if search_terms:
                result = await self.send_mcp_request("retrieve_memories", {
                    "agent_name": self.config.name,
                    "related_to_tags": " ".join(search_terms),
                    "limit": 5
                })
                
                if result.get("success"):
                    return result.get("data", [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def _maybe_store_memory(self, user_message: str, ai_response: str, user_from: str):
        """Store important information in agent memory."""
        try:
            # Simple heuristics to determine if something should be remembered
            should_store = (
                len(user_message) > 50 or  # Substantial messages
                "remember" in user_message.lower() or
                "important" in user_message.lower() or
                any(word in user_message.lower() for word in ["project", "analysis", "report", "data"])
            )
            
            if should_store:
                memory_label = self._generate_memory_label(user_message)
                memory_content = f"User ({user_from}) asked: {user_message[:200]}... My response: {ai_response[:200]}..."
                tags = self._extract_search_terms(user_message)
                
                await self.send_mcp_request("store_memory", {
                    "agent_name": self.config.name,
                    "memory_label": memory_label,
                    "memory_content": memory_content,
                    "related_to_tags": " ".join(tags)
                })
                
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
    
    def _extract_search_terms(self, text: str) -> List[str]:
        """Extract key terms for memory search."""
        # Simple keyword extraction
        important_words = []
        words = text.lower().split()
        
        # Filter out common words and keep potentially important ones
        skip_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "you", "me", "i", "we", "they", "them", "this", "that", "these", "those"}
        
        for word in words:
            if len(word) > 3 and word not in skip_words:
                important_words.append(word)
        
        return important_words[:5]  # Return top 5 terms
    
    def _generate_memory_label(self, user_message: str) -> str:
        """Generate a label for the memory."""
        words = user_message.split()[:6]  # First 6 words
        return " ".join(words) + ("..." if len(user_message.split()) > 6 else "")
    
    async def run_polling_cycle(self):
        """Run one polling cycle - check messages and respond."""
        try:
            # Check for new messages
            messages = await self.check_for_messages()
            
            if messages:
                self.logger.info(f"Found {len(messages)} new messages")
                
                # Process each message
                message_ids_to_mark = []
                
                for message in messages:
                    try:
                        # Process the message
                        response = await self.process_message(message)
                        
                        # Send response back to user
                        user_from = message.get("User_From")
                        await self.send_response(response, user_from)
                        
                        # Mark message for reading
                        message_id = message.get("Message_ID")
                        if message_id:
                            message_ids_to_mark.append(message_id)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing individual message: {e}")
                
                # Mark all processed messages as read
                if message_ids_to_mark:
                    await self.mark_messages_read(message_ids_to_mark)
            
        except Exception as e:
            self.logger.error(f"Error in polling cycle: {e}")
    
    async def run(self):
        """Main agent loop."""
        self.logger.info(f"Starting agent {self.config.name}")
        
        # Test Ollama connection
        if not self.ollama.test_connection():
            self.logger.error("Cannot connect to Ollama. Make sure Ollama is running.")
            return
        
        # Connect to messaging server
        if not await self.connect_to_server():
            self.logger.error("Failed to connect to messaging server")
            return
        
        self.running = True
        self.logger.info(f"Agent {self.config.name} is now active and polling for messages")
        
        try:
            while self.running:
                await self.run_polling_cycle()
                await asyncio.sleep(self.config.polling_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            await self.disconnect()
            self.logger.info(f"Agent {self.config.name} stopped")
    
    def stop(self):
        """Stop the agent."""
        self.running = False


class AgentManager:
    """Manages multiple AI agents."""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.agents = {}
        self.tasks = []
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file {self.config_file} not found")
            return {}
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            return {}
    
    def create_agents_from_config(self, config: Dict[str, Any]) -> List[AgentConfig]:
        """Create agent configurations from config file."""
        agents = []
        
        # Default agents if none specified
        default_agents = [
            {
                "name": "DataAnalyst",
                "description": "Analyzes data and generates reports",
                "model_api": "ollama",
                "model": "qwen2.5-coder"
            },
            {
                "name": "QueryBot", 
                "description": "Executes database queries and explains results",
                "model_api": "ollama",
                "model": "qwen2.5-coder"
            },
            {
                "name": "ReportGen",
                "description": "Generates business reports from data", 
                "model_api": "ollama",
                "model": "qwen2.5-coder"
            }
        ]
        
        # Use config agents or default
        agent_configs = config.get("agents", default_agents)
        
        for agent_config in agent_configs:
            agents.append(AgentConfig(
                name=agent_config["name"],
                description=agent_config["description"],
                model_api=agent_config.get("model_api", "ollama"),
                model=agent_config.get("model", "qwen2.5-coder"),
                api_key=agent_config.get("api_key"),
                polling_interval=agent_config.get("polling_interval", 3)
            ))
        
        return agents
    
    async def start_agents(self):
        """Start all configured agents."""
        config = self.load_config()
        agent_configs = self.create_agents_from_config(config)
        
        if not agent_configs:
            logging.error("No agents configured")
            return
        
        # Create and start agents
        for agent_config in agent_configs:
            agent = TriAIAgent(agent_config)
            self.agents[agent_config.name] = agent
            
            # Start agent in background task
            task = asyncio.create_task(agent.run())
            self.tasks.append(task)
            
            logging.info(f"Started agent: {agent_config.name}")
            
            # Small delay between agent starts
            await asyncio.sleep(1)
    
    async def stop_agents(self):
        """Stop all agents."""
        logging.info("Stopping all agents...")
        
        # Stop all agents
        for agent in self.agents.values():
            agent.stop()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logging.info("All agents stopped")
    
    async def run(self):
        """Run the agent manager."""
        def signal_handler(signum, frame):
            logging.info("Received shutdown signal")
            for agent in self.agents.values():
                agent.stop()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            await self.start_agents()
            
            # Wait for all agents to complete
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
                
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt")
        finally:
            await self.stop_agents()


async def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = AgentManager()
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())