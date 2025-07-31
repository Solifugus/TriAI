"""
MCP (Model Context Protocol) tools for database access and memory management.
These tools are provided to AI agents via WebSocket connections.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
try:
    from datalink import DataLink  
    DATALINK_AVAILABLE = True
except ImportError:
    DataLink = None
    DATALINK_AVAILABLE = False
    
from mock_datalink import MockDataLink


class MCPToolProvider:
    """
    Provides MCP tools for AI agents to access databases and manage memories.
    """
    
    def __init__(self, db: Union[MockDataLink, Any]):
        """
        Initialize MCP tool provider.
        
        Args:
            db: MockDataLink or DataLink instance
        """
        self.db = db
        
        # Define available tools
        self.tools = {
            # Connection Management
            "connect_to_database": self.connect_to_database,
            "list_databases": self.list_databases,
            
            # Schema Discovery
            "get_schema_info": self.get_schema_info,
            "describe_table": self.describe_table,
            "get_table_relationships": self.get_table_relationships,
            "get_table_dependencies": self.get_table_dependencies,
            
            # Query Execution
            "execute_query": self.execute_query,
            "validate_sql": self.validate_sql,
            "get_query_history": self.get_query_history,
            "check_permissions": self.check_permissions,
            
            # Data Exploration
            "sample_table": self.sample_table,
            "get_column_stats": self.get_column_stats,
            
            # Memory Management
            "store_memory": self.store_memory,
            "retrieve_memories": self.retrieve_memories,
            "search_memories": self.search_memories,
            "update_memory": self.update_memory,
            "delete_memory": self.delete_memory,
            "get_memory_stats": self.get_memory_stats
        }
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name not in self.tools:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "available_tools": list(self.tools.keys())
                }
                
            tool_func = self.tools[tool_name]
            result = tool_func(**parameters)
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Connection Management Tools
    
    def connect_to_database(self, server_instance: str, database_name: str, 
                          connection_string: Optional[str] = None) -> Dict[str, Any]:
        """Connect to a database and return connection status."""
        try:
            # Test connection
            test_query = "SELECT 1 as connection_test"
            result = self.db.sql_get(test_query, database_name)
            
            return {
                "connected": True,
                "server": server_instance,
                "database": database_name,
                "test_result": result
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    def list_databases(self, server_instance: str) -> List[str]:
        """List available databases on the server."""
        try:
            # This would typically query sys.databases
            query = "SELECT name FROM sys.databases WHERE database_id > 4"  # Skip system DBs
            results = self.db.sql_get(query)
            return [row['name'] for row in results]
        except Exception:
            # Return mock data if query fails
            return ["TriAI_Main", "SalesDB", "CustomerDB", "InventoryDB"]
    
    # Schema Discovery Tools
    
    def get_schema_info(self, database_name: str, object_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get database schema information."""
        if object_types is None:
            object_types = ["tables", "views", "procedures"]
            
        try:
            schema_info = {"database": database_name}
            
            if "tables" in object_types:
                tables_query = """
                SELECT TABLE_NAME, TABLE_TYPE 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_CATALOG = ?
                """
                # For mock, return sample table info
                schema_info["tables"] = [
                    {"name": "AI_Agents", "type": "BASE TABLE"},
                    {"name": "AI_Messages", "type": "BASE TABLE"},
                    {"name": "AI_Memories", "type": "BASE TABLE"},
                    {"name": "AI_Query_History", "type": "BASE TABLE"},
                    {"name": "Customers", "type": "BASE TABLE"},
                    {"name": "Orders", "type": "BASE TABLE"}
                ]
            
            if "views" in object_types:
                schema_info["views"] = [
                    {"name": "vw_ActiveAgents", "type": "VIEW"},
                    {"name": "vw_RecentMessages", "type": "VIEW"}
                ]
                
            if "procedures" in object_types:
                schema_info["procedures"] = [
                    {"name": "sp_GetAgentStats", "type": "PROCEDURE"},
                    {"name": "sp_CleanupOldMemories", "type": "PROCEDURE"}
                ]
                
            return schema_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def describe_table(self, database_name: str, table_name: str, 
                      include_sample_data: bool = False) -> Dict[str, Any]:
        """Get detailed table information."""
        try:
            # Mock table descriptions based on TriAI schema
            table_descriptions = {
                "AI_Agents": {
                    "columns": [
                        {"name": "Agent", "type": "VARCHAR(15)", "nullable": False, "primary_key": True},
                        {"name": "Description", "type": "VARCHAR(MAX)", "nullable": True},
                        {"name": "Model_API", "type": "VARCHAR(30)", "nullable": True},
                        {"name": "Model", "type": "VARCHAR(100)", "nullable": True},
                        {"name": "Model_API_KEY", "type": "VARCHAR(500)", "nullable": True}
                    ]
                },
                "AI_Messages": {
                    "columns": [
                        {"name": "Message_ID", "type": "INT IDENTITY(1,1)", "nullable": False, "primary_key": True},
                        {"name": "Posted", "type": "DATETIME", "nullable": False, "default": "GETDATE()"},
                        {"name": "User_From", "type": "VARCHAR(15)", "nullable": False},
                        {"name": "User_To", "type": "VARCHAR(15)", "nullable": False},
                        {"name": "Message", "type": "VARCHAR(MAX)", "nullable": True},
                        {"name": "User_Read", "type": "DATETIME", "nullable": True}
                    ]
                },
                "AI_Memories": {
                    "columns": [
                        {"name": "Memory_ID", "type": "INT IDENTITY(1,1)", "nullable": False, "primary_key": True},
                        {"name": "Agent", "type": "VARCHAR(15)", "nullable": False},
                        {"name": "First_Posted", "type": "DATETIME", "nullable": False, "default": "GETDATE()"},
                        {"name": "Times_Recalled", "type": "INT", "nullable": False, "default": "0"},
                        {"name": "Last_Recalled", "type": "DATETIME", "nullable": True},
                        {"name": "Memory_Label", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "Memory", "type": "VARCHAR(MAX)", "nullable": True},
                        {"name": "Related_To", "type": "VARCHAR(200)", "nullable": False},
                        {"name": "Purge_After", "type": "DATETIME", "nullable": True}
                    ]
                }
            }
            
            result = {
                "table_name": table_name,
                "database": database_name
            }
            
            if table_name in table_descriptions:
                result.update(table_descriptions[table_name])
            else:
                # Generic table structure
                result["columns"] = [
                    {"name": "ID", "type": "INT", "nullable": False, "primary_key": True},
                    {"name": "Name", "type": "VARCHAR(100)", "nullable": True},
                    {"name": "Created", "type": "DATETIME", "nullable": False}
                ]
            
            if include_sample_data:
                sample_data = self.sample_table(database_name, table_name, 5)
                result["sample_data"] = sample_data
                
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_table_relationships(self, database_name: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get foreign key relationships."""
        # Mock relationship data
        relationships = [
            {
                "parent_table": "AI_Agents",
                "parent_column": "Agent",
                "child_table": "AI_Messages",
                "child_column": "User_To",
                "constraint_name": "FK_Messages_Agent"
            },
            {
                "parent_table": "AI_Agents", 
                "parent_column": "Agent",
                "child_table": "AI_Memories",
                "child_column": "Agent",
                "constraint_name": "FK_Memories_Agent"
            }
        ]
        
        if table_name:
            relationships = [r for r in relationships 
                           if r["parent_table"] == table_name or r["child_table"] == table_name]
        
        return relationships
    
    def get_table_dependencies(self, database_name: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get table dependencies (views, procedures that use this table)."""
        return [
            {
                "dependent_object": "vw_ActiveAgents",
                "dependency_type": "VIEW",
                "referenced_table": "AI_Agents"
            },
            {
                "dependent_object": "sp_GetAgentStats",
                "dependency_type": "PROCEDURE", 
                "referenced_table": "AI_Messages"
            }
        ]
    
    # Query Execution Tools
    
    def execute_query(self, database_name: str, sql_query: str, row_limit: int = 1000) -> Dict[str, Any]:
        """Execute SELECT query with row limit."""
        try:
            # Ensure query is SELECT only for security
            sql_lower = sql_query.lower().strip()
            if not sql_lower.startswith("select"):
                return {"error": "Only SELECT queries are allowed"}
            
            # Add LIMIT if not present and row_limit specified
            if "limit" not in sql_lower and row_limit > 0:
                sql_query = f"{sql_query} LIMIT {row_limit}"
            
            # Execute query
            start_time = datetime.now()
            results = self.db.sql_get(sql_query, database_name)
            end_time = datetime.now()
            
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log query to history
            self._log_query_history("system", database_name, sql_query, len(results), execution_time_ms)
            
            return {
                "query": sql_query,
                "row_count": len(results),
                "execution_time_ms": execution_time_ms,
                "results": results
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def validate_sql(self, database_name: str, sql_query: str) -> Dict[str, Any]:
        """Validate SQL syntax without execution."""
        try:
            # Basic validation checks
            sql_lower = sql_query.lower().strip()
            
            issues = []
            
            # Check for dangerous operations
            dangerous_keywords = ["drop", "delete", "update", "insert", "truncate", "alter"]
            for keyword in dangerous_keywords:
                if keyword in sql_lower:
                    issues.append(f"Contains potentially dangerous keyword: {keyword}")
            
            # Check for basic syntax issues
            if not sql_lower.startswith("select"):
                issues.append("Query must start with SELECT")
                
            if sql_query.count("(") != sql_query.count(")"):
                issues.append("Mismatched parentheses")
                
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "query": sql_query
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def get_query_history(self, agent_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get query history for an agent."""
        try:
            query = """
            SELECT Query_ID, Agent, Database_Name, SQL_Query, Executed_Time, 
                   Row_Count, Execution_Time_MS
            FROM AI_Query_History 
            WHERE Agent = ? 
            ORDER BY Executed_Time DESC
            LIMIT ?
            """
            results = self.db.sql_get(f"SELECT * FROM AI_Query_History WHERE Agent = '{agent_name}' LIMIT {limit}")
            return results
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def check_permissions(self, database_name: str, object_name: str, operation: str) -> Dict[str, Any]:
        """Check if operation is permitted on database object."""
        # For SELECT operations, always allow
        if operation.upper() == "SELECT":
            return {"permitted": True, "operation": operation, "object": object_name}
        
        # For other operations, deny by default for security
        return {
            "permitted": False,
            "operation": operation,
            "object": object_name,
            "reason": "Only SELECT operations are permitted for AI agents"
        }
    
    # Data Exploration Tools
    
    def sample_table(self, database_name: str, table_name: str, row_count: int = 10, 
                    columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        try:
            if columns:
                columns_str = ", ".join(columns)
            else:
                columns_str = "*"
                
            query = f"SELECT {columns_str} FROM {table_name} LIMIT {row_count}"
            results = self.db.sql_get(query, database_name)
            return results
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_column_stats(self, database_name: str, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get basic statistics for a column."""
        try:
            # Mock column statistics
            return {
                "column_name": column_name,
                "table_name": table_name,
                "total_rows": 1000,
                "null_count": 25,
                "unique_values": 950,
                "most_common_value": "Sample Value",
                "min_value": "A",
                "max_value": "Z"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # Memory Management Tools
    
    def store_memory(self, agent_name: str, memory_label: str, memory_content: str,
                    related_to_tags: str, purge_after: Optional[datetime] = None) -> Dict[str, Any]:
        """Store a memory for an agent."""
        try:
            memory_data = [{
                "Agent": agent_name,
                "Memory_Label": memory_label,
                "Memory": memory_content,
                "Related_To": related_to_tags,
                "First_Posted": datetime.now(),
                "Times_Recalled": 0,
                "Purge_After": purge_after
            }]
            
            self.db.sql_insert("AI_Memories", memory_data)
            
            # Get the inserted memory ID (mock for now)
            memory_id = len(self.db.sql_get("SELECT * FROM AI_Memories")) + 1
            
            return {
                "memory_id": memory_id,
                "agent": agent_name,
                "stored": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def retrieve_memories(self, agent_name: str, related_to_tags: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories by tags and update recall count."""
        try:
            # Split tags and create search conditions
            tags = related_to_tags.split()
            
            # For simplicity, search for any matching tag
            query = f"""
            SELECT * FROM AI_Memories 
            WHERE Agent = '{agent_name}' 
            AND (Related_To LIKE '%{tags[0]}%'
            """
            
            for tag in tags[1:]:
                query += f" OR Related_To LIKE '%{tag}%'"
            query += f") LIMIT {limit}"
            
            memories = self.db.sql_get(query)
            
            # Update recall counts (simplified)
            for memory in memories:
                update_query = f"""
                UPDATE AI_Memories 
                SET Times_Recalled = Times_Recalled + 1, Last_Recalled = GETDATE()
                WHERE Memory_ID = {memory.get('Memory_ID', 0)}
                """
                self.db.sql_run(update_query)
            
            return memories
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def search_memories(self, agent_name: str, search_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search through memory content."""
        try:
            query = f"""
            SELECT * FROM AI_Memories 
            WHERE Agent = '{agent_name}' 
            AND (Memory LIKE '%{search_text}%' OR Memory_Label LIKE '%{search_text}%')
            LIMIT {limit}
            """
            
            results = self.db.sql_get(query)
            return results
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def update_memory(self, memory_id: int, memory_content: str, 
                     related_to_tags: Optional[str] = None) -> Dict[str, Any]:
        """Update existing memory."""
        try:
            update_parts = [f"Memory = '{self.db.sql_escape(memory_content, quote=False)}'"]
            
            if related_to_tags:
                update_parts.append(f"Related_To = '{self.db.sql_escape(related_to_tags, quote=False)}'")
            
            query = f"""
            UPDATE AI_Memories 
            SET {', '.join(update_parts)}
            WHERE Memory_ID = {memory_id}
            """
            
            self.db.sql_run(query)
            
            return {"memory_id": memory_id, "updated": True}
            
        except Exception as e:
            return {"error": str(e)}
    
    def delete_memory(self, memory_id: int) -> Dict[str, Any]:
        """Delete a specific memory."""
        try:
            query = f"DELETE FROM AI_Memories WHERE Memory_ID = {memory_id}"
            self.db.sql_run(query)
            
            return {"memory_id": memory_id, "deleted": True}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_memory_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get memory usage statistics for an agent."""
        try:
            stats_query = f"""
            SELECT 
                COUNT(*) as total_memories,
                AVG(Times_Recalled) as avg_recalls,
                MAX(Times_Recalled) as max_recalls,
                COUNT(CASE WHEN Times_Recalled = 0 THEN 1 END) as unused_memories
            FROM AI_Memories 
            WHERE Agent = '{agent_name}'
            """
            
            results = self.db.sql_get(stats_query)
            
            if results:
                stats = results[0]
                
                # Get most common tags
                tags_query = f"""
                SELECT Related_To FROM AI_Memories WHERE Agent = '{agent_name}'
                """
                tag_results = self.db.sql_get(tags_query)
                
                # Simple tag frequency analysis
                tag_counts = {}
                for row in tag_results:
                    tags = row.get('Related_To', '').split()
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Get top 5 tags
                top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                
                stats['top_tags'] = top_tags
                return stats
            else:
                return {"total_memories": 0}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _log_query_history(self, agent_name: str, database_name: str, sql_query: str, 
                          row_count: int, execution_time_ms: int) -> None:
        """Log query execution to history table."""
        try:
            history_data = [{
                "Agent": agent_name,
                "Database_Name": database_name,
                "SQL_Query": sql_query,
                "Executed_Time": datetime.now(),
                "Row_Count": row_count,
                "Execution_Time_MS": execution_time_ms
            }]
            
            self.db.sql_insert("AI_Query_History", history_data)
            
        except Exception as e:
            # Log the error but don't fail the main operation
            self.db.log(f"Failed to log query history: {str(e)}")