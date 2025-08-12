"""
Enhanced TriAI Agent Server that properly uses MCP tools for database queries.
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
import re


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    description: str
    role: str
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


class EnhancedTriAIAgent:
    """
    Enhanced AI Agent that properly uses MCP tools for database operations.
    """
    
    def __init__(self, config: AgentConfig, server_url: str = "ws://localhost:8080"):
        self.config = config
        self.server_url = server_url
        self.websocket = None
        self.running = False
        self.ollama = OllamaClient()
        self.available_mcp_tools = []
        self.memory_cache = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format=f'[{config.name}] %(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"Agent-{config.name}")
        
        # Enhanced system prompt that encourages MCP tool usage
        self.system_prompt = self._create_enhanced_system_prompt()
        
    def _create_enhanced_system_prompt(self) -> str:
        """Create enhanced system prompt that encourages proper MCP tool usage."""
        base_prompt = f"""You are {self.config.name}, an AI assistant specialized in: {self.config.description}

Your role: {self.config.role}

IMPORTANT - YOU HAVE DIRECT DATABASE ACCESS:
You have access to MCP (Model Context Protocol) tools that allow you to:
- Execute SELECT queries on databases using execute_query
- Explore database schemas using get_schema_info and describe_table
- Store and retrieve memories using store_memory and retrieve_memories
- Analyze data patterns and generate insights

BEHAVIOR GUIDELINES:
1. When users ask about data, DON'T offer to help them write queries - EXECUTE THE QUERIES YOURSELF
2. Use execute_query to run SELECT statements and get actual data
3. Use describe_table to understand table structures before querying
4. Store important findings in memories for future reference
5. Be proactive - if you can answer a question by querying data, DO IT

Example interaction flow:
User: "How many customers do we have?"
You: "Let me check that for you." [Execute: SELECT COUNT(*) FROM Customers]
You: "Based on our database, we currently have 1,247 active customers."

NOT this:
User: "How many customers do we have?" 
You: "I can help you write a query like SELECT COUNT(*) FROM Customers"

ALWAYS be helpful by DOING rather than just suggesting. You are an AI agent with database access - use it!
"""
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
                self.available_mcp_tools = data.get("available_tools", [])
                self.logger.info(f"Available MCP tools: {len(self.available_mcp_tools)}")
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
            
            self.logger.debug(f"Sending MCP request: {tool} with params: {parameters}")
            await self.websocket.send(json.dumps(request))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=30)
            
            result = json.loads(response)
            self.logger.debug(f"MCP response: {result.get('success', False)}")
            return result
            
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
                message = {
                    "User_From": data.get("from"),
                    "Message": data.get("message"),
                    "Message_ID": None,
                    "Posted": data.get("timestamp")
                }
                return [message]
            elif data.get("type") in ["send_response_ack", "mcp_response"]:
                return []
            else:
                self.logger.warning(f"Unexpected response to message check: {data}")
                return []
                
        except asyncio.TimeoutError:
            self.logger.error("Failed to check messages: Timeout waiting for server response")
            return []
        except Exception as e:
            self.logger.error(f"Failed to check messages: {type(e).__name__}: {e}")
            return []
    
    async def mark_messages_read(self, message_ids: List[int]):
        """Mark messages as read."""
        try:
            request = {
                "type": "mark_read",
                "message_ids": message_ids
            }
            await self.websocket.send(json.dumps(request))
            await asyncio.wait_for(self.websocket.recv(), timeout=10)
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
            
            # Wait for acknowledgment
            for attempt in range(3):
                response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("success") or data.get("type") == "send_response_ack":
                    self.logger.info(f"Response sent to {to_user}")
                    return
                elif data.get("type") in ["messages_response", "mcp_response"]:
                    continue
                else:
                    self.logger.error(f"Failed to send response: {data}")
                    return
                    
        except Exception as e:
            self.logger.error(f"Failed to send response: {e}")
    
    async def process_message(self, message: Dict[str, Any]) -> str:
        """Process a user message and generate AI response with MCP tool integration."""
        try:
            user_message = message.get("Message", "")
            user_from = message.get("User_From", "user")
            
            self.logger.info(f"Processing message from {user_from}: {user_message[:100]}...")
            
            # First, check if this is a data-related question that requires MCP tools
            if self._requires_database_access(user_message):
                # Handle database query directly
                enhanced_response = await self._handle_database_query(user_message, user_from)
                if enhanced_response:
                    return enhanced_response
            
            # Retrieve relevant memories
            memories = await self._get_relevant_memories(user_message)
            memory_context = self._format_memories_for_context(memories)
            
            # Build prompt with context and MCP tool availability
            full_prompt = self._build_enhanced_prompt(user_message, memory_context)
            
            # Generate response using Ollama
            ai_response = await self.ollama.generate(
                model=self.config.model,
                prompt=full_prompt,
                system_prompt=self.system_prompt
            )
            
            # Store important information in memory
            await self._maybe_store_memory(user_message, ai_response, user_from)
            
            return ai_response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"I apologize, but I encountered an error while processing your message: {str(e)}"
    
    def _requires_database_access(self, user_message: str) -> bool:
        """Determine if the user message requires database access."""
        data_keywords = [
            # Direct data requests
            "how many", "count", "total", "sum", "average", "show me", "list", "find",
            # Data analysis terms
            "analyze", "report", "data", "information", "statistics", "metrics",
            # Database objects
            "customer", "member", "user", "account", "transaction", "order", "product",
            "loan", "payment", "record", "table", "database",
            # Question words that often lead to data queries
            "what", "which", "who", "where", "when"
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in data_keywords)
    
    async def _handle_database_query(self, user_message: str, user_from: str) -> Optional[str]:
        """Handle database queries proactively."""
        try:
            self.logger.info(f"Handling database query for: {user_message[:100]}...")
            
            # First, get schema information to understand available tables
            schema_result = await self.send_mcp_request("get_schema_info", {
                "database_name": self._get_database_name()
            })
            
            if not schema_result.get("success"):
                return None
            
            tables = schema_result.get("data", {}).get("tables", [])
            table_names = [table["name"] for table in tables]
            
            # Analyze user message to determine what they're looking for
            query_intent = self._analyze_query_intent(user_message, table_names)
            
            if query_intent:
                # Execute the query
                query_result = await self.send_mcp_request("execute_query", {
                    "database_name": self._get_database_name(),
                    "sql_query": query_intent["query"],
                    "row_limit": 100
                })
                
                if query_result.get("success"):
                    data = query_result.get("data", {})
                    results = data.get("results", [])
                    
                    if results:
                        formatted_results = self._format_query_results(results, query_intent["context"])
                        response = f"Based on our database, here's what I found:\n\n{formatted_results}"
                        
                        # Store this query in memory
                        await self._store_query_memory(user_message, query_intent["query"], results, user_from)
                        
                        return response
                    else:
                        return f"I executed a query to find {query_intent['context']}, but no results were returned. The data might not be available or the search criteria might be too specific."
                else:
                    error_msg = query_result.get("error", "Unknown error")
                    return f"I tried to query the database for {query_intent['context']}, but encountered an error: {error_msg}"
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error handling database query: {e}")
            return None
    
    def _get_database_name(self) -> str:
        """Get the appropriate database name based on context."""
        # This could be made configurable or dynamic
        return "TriAI_Main"  # Default database name
    
    def _analyze_query_intent(self, user_message: str, available_tables: List[str]) -> Optional[Dict[str, str]]:
        """Analyze user message to determine query intent and generate appropriate SQL."""
        message_lower = user_message.lower()
        
        # Simple pattern matching for common query types
        patterns = [
            {
                "pattern": r"how many (.*?) (are there|do we have|exist)",
                "template": "SELECT COUNT(*) as total FROM {table}",
                "table_hints": ["customer", "member", "user", "account", "order", "transaction"]
            },
            {
                "pattern": r"show me (.*?) (data|information|records)",
                "template": "SELECT TOP 10 * FROM {table}",
                "table_hints": ["customer", "member", "account", "order", "transaction"]
            },
            {
                "pattern": r"(list|show) (all|the) (.*)",
                "template": "SELECT TOP 20 * FROM {table}",
                "table_hints": ["customer", "member", "account", "product", "order"]
            },
            {
                "pattern": r"what (.*?) (do we have|are available)",
                "template": "SELECT DISTINCT {column} FROM {table}",
                "table_hints": ["product", "category", "type", "status"]
            }
        ]
        
        for pattern_info in patterns:
            match = re.search(pattern_info["pattern"], message_lower)
            if match:
                # Find the most relevant table
                relevant_table = self._find_relevant_table(match.groups(), available_tables, pattern_info["table_hints"])
                
                if relevant_table:
                    query = pattern_info["template"].format(table=relevant_table, column="*")
                    context = f"{match.group(1)} from {relevant_table}"
                    
                    return {
                        "query": query,
                        "context": context,
                        "table": relevant_table
                    }
        
        # Fallback: if message mentions a specific table name
        for table in available_tables:
            if table.lower() in message_lower:
                return {
                    "query": f"SELECT TOP 10 * FROM {table}",
                    "context": f"data from {table}",
                    "table": table
                }
        
        return None
    
    def _find_relevant_table(self, match_groups: tuple, available_tables: List[str], hints: List[str]) -> Optional[str]:
        """Find the most relevant table based on user message and hints."""
        # Check if any table name is mentioned in the match groups
        for group in match_groups:
            if group:
                for table in available_tables:
                    if table.lower() in group.lower() or group.lower() in table.lower():
                        return table
        
        # Check hints against available tables
        for hint in hints:
            for table in available_tables:
                if hint in table.lower() or table.lower() in hint:
                    return table
        
        # Return the first available table as fallback
        return available_tables[0] if available_tables else None
    
    def _format_query_results(self, results: List[Dict[str, Any]], context: str = "") -> str:
        """Format query results for display to user."""
        if not results:
            return "No data found."
        
        # For simple count queries
        if len(results) == 1 and len(results[0]) == 1:
            key, value = list(results[0].items())[0]
            if "total" in key.lower() or "count" in key.lower():
                return f"Total: {value:,}"
        
        # For multiple rows, show in a readable format
        output = []
        
        if len(results) <= 5:
            # Show all results if few
            for i, row in enumerate(results, 1):
                row_info = []
                for key, value in row.items():
                    if value is not None:
                        if isinstance(value, (int, float)) and key.lower() in ['amount', 'balance', 'price', 'cost']:
                            row_info.append(f"{key}: ${value:,.2f}")
                        elif isinstance(value, (int, float)):
                            row_info.append(f"{key}: {value:,}")
                        else:
                            row_info.append(f"{key}: {value}")
                
                output.append(f"{i}. {' | '.join(row_info)}")
        else:
            # Summarize if many results
            output.append(f"Found {len(results)} records. Here are the first 3:")
            for i, row in enumerate(results[:3], 1):
                row_summary = []
                for key, value in list(row.items())[:3]:  # Show first 3 columns
                    if value is not None:
                        row_summary.append(f"{key}: {value}")
                output.append(f"{i}. {' | '.join(row_summary)}")
            
            if len(results) > 3:
                output.append(f"... and {len(results) - 3} more records")
        
        return "\n".join(output)
    
    async def _store_query_memory(self, user_question: str, sql_query: str, results: List[Dict], user_from: str):
        """Store successful queries in agent memory."""
        try:
            memory_label = f"Query: {user_question[:50]}..."
            memory_content = f"User {user_from} asked: {user_question}\nSQL used: {sql_query}\nResults: {len(results)} records returned"
            
            await self.send_mcp_request("store_memory", {
                "agent_name": self.config.name,
                "memory_label": memory_label,
                "memory_content": memory_content,
                "related_to_tags": "database query sql data analysis"
            })
        except Exception as e:
            self.logger.error(f"Error storing query memory: {e}")
    
    def _build_enhanced_prompt(self, user_message: str, memory_context: str) -> str:
        """Build enhanced prompt that encourages MCP tool usage."""
        prompt = f"User message: {user_message}\n\n"
        
        if memory_context:
            prompt += f"Relevant memories from past conversations:\n{memory_context}\n\n"
        
        prompt += """Remember: You have direct database access through MCP tools. If the user is asking about data:
1. Use execute_query to run SELECT statements
2. Use describe_table to understand table structure
3. Be proactive - query the database directly rather than asking the user to write queries

Provide a helpful response that uses your capabilities to directly answer their question."""
        
        return prompt
    
    async def _get_relevant_memories(self, user_message: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on user message."""
        try:
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
    
    def _format_memories_for_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for inclusion in prompt context."""
        if not memories:
            return ""
        
        context_parts = []
        for memory in memories[:3]:
            label = memory.get("memory_label", "Memory")
            content = memory.get("memory", "")
            context_parts.append(f"- {label}: {content}")
        
        return "\n".join(context_parts)
    
    async def _maybe_store_memory(self, user_message: str, ai_response: str, user_from: str):
        """Store important information in agent memory."""
        try:
            should_store = (
                len(user_message) > 30 or
                "remember" in user_message.lower() or
                "important" in user_message.lower() or
                any(word in user_message.lower() for word in ["analysis", "report", "data", "query"])
            )
            
            if should_store:
                memory_label = self._generate_memory_label(user_message)
                memory_content = f"User ({user_from}): {user_message[:200]}... Response: {ai_response[:200]}..."
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
        important_words = []
        words = text.lower().split()
        
        skip_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "you", "me", "i", "we", "they", "them", "this", "that", "these", "those"}
        
        for word in words:
            if len(word) > 3 and word not in skip_words:
                important_words.append(word)
        
        return important_words[:5]
    
    def _generate_memory_label(self, user_message: str) -> str:
        """Generate a label for the memory."""
        words = user_message.split()[:6]
        return " ".join(words) + ("..." if len(user_message.split()) > 6 else "")
    
    async def run_polling_cycle(self):
        """Run one polling cycle - check messages and respond."""
        try:
            messages = await self.check_for_messages()
            
            if messages:
                self.logger.info(f"Found {len(messages)} new messages")
                
                message_ids_to_mark = []
                
                for message in messages:
                    try:
                        response = await self.process_message(message)
                        
                        user_from = message.get("User_From")
                        await self.send_response(response, user_from)
                        
                        message_id = message.get("Message_ID")
                        if message_id:
                            message_ids_to_mark.append(message_id)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing individual message: {e}")
                
                if message_ids_to_mark:
                    await self.mark_messages_read(message_ids_to_mark)
            
        except Exception as e:
            self.logger.error(f"Error in polling cycle: {e}")
    
    async def run(self):
        """Main agent loop."""
        self.logger.info(f"Starting enhanced agent {self.config.name}")
        
        if not self.ollama.test_connection():
            self.logger.error("Cannot connect to Ollama. Make sure Ollama is running.")
            return
        
        if not await self.connect_to_server():
            self.logger.error("Failed to connect to messaging server")
            return
        
        self.running = True
        self.logger.info(f"Enhanced agent {self.config.name} is active with MCP database access")
        
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
            self.logger.info(f"Enhanced agent {self.config.name} stopped")
    
    def stop(self):
        """Stop the agent."""
        self.running = False


def load_agent_config_from_database() -> List[AgentConfig]:
    """Load agent configurations from database instead of config file."""
    # This would connect to the database and load agents from AI_Agents table
    # For now, return some default agents
    return [
        AgentConfig(
            name="DataAnalyst",
            description="Analyzes database information and generates reports",
            role="You are a data analyst who proactively queries databases to answer user questions about business data, customer information, and analytics.",
            model_api="ollama",
            model="qwen2.5-coder",
            polling_interval=3
        ),
        AgentConfig(
            name="QueryBot",
            description="Executes database queries and explains results", 
            role="You are a database query specialist who directly executes SQL queries to retrieve and analyze data for users.",
            model_api="ollama",
            model="qwen2.5-coder",
            polling_interval=3
        )
    ]


async def main():
    """Main entry point for enhanced agent server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load agent configurations
    agent_configs = load_agent_config_from_database()
    
    agents = []
    tasks = []
    
    # Create and start agents
    for config in agent_configs:
        agent = EnhancedTriAIAgent(config)
        agents.append(agent)
        
        task = asyncio.create_task(agent.run())
        tasks.append(task)
        
        logging.info(f"Started enhanced agent: {config.name}")
        await asyncio.sleep(1)  # Small delay between starts
    
    def signal_handler(signum, frame):
        logging.info("Received shutdown signal")
        for agent in agents:
            agent.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    finally:
        for agent in agents:
            agent.stop()
        logging.info("All enhanced agents stopped")


if __name__ == "__main__":
    asyncio.run(main())