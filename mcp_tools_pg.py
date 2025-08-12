"""
PostgreSQL-compatible MCP (Model Context Protocol) tools for database access and memory management.
These tools are provided to AI agents via WebSocket connections.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pg_datalink import PostgreSQLDataLink

class PostgreSQLMCPToolProvider:
    """
    Provides MCP tools for AI agents to access PostgreSQL databases and manage memories.
    """
    
    def __init__(self, db: PostgreSQLDataLink):
        """
        Initialize MCP tool provider.
        
        Args:
            db: PostgreSQLDataLink instance
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
            if self.db.test_connection():
                test_result = self.db.sql_get("SELECT current_database(), current_user")
                return {
                    "connected": True,
                    "server": server_instance,
                    "database": database_name,
                    "current_database": test_result[0]["current_database"],
                    "current_user": test_result[0]["current_user"]
                }
            else:
                return {
                    "connected": False,
                    "error": "Database connection test failed"
                }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    def list_databases(self, server_instance: str) -> List[str]:
        """List available databases on the server."""
        try:
            # PostgreSQL query to list databases
            query = "SELECT datname FROM pg_database WHERE datallowconn = TRUE ORDER BY datname"
            results = self.db.sql_get(query)
            return [row['datname'] for row in results]
        except Exception as e:
            # Return current database if query fails
            try:
                current_db = self.db.sql_get("SELECT current_database()")[0]["current_database"]
                return [current_db]
            except:
                return ["triai_test"]
    
    # Schema Discovery Tools
    
    def get_schema_info(self, database_name: str, object_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get database schema information."""
        if object_types is None:
            object_types = ["tables", "views"]
            
        try:
            schema_info = {"database": database_name}
            
            if "tables" in object_types:
                tables_query = """
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
                results = self.db.sql_get(tables_query)
                schema_info["tables"] = [
                    {"name": row["table_name"], "type": row["table_type"]} 
                    for row in results
                ]
            
            if "views" in object_types:
                views_query = """
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
                results = self.db.sql_get(views_query)
                schema_info["views"] = [
                    {"name": row["table_name"], "type": "VIEW"} 
                    for row in results
                ]
                
            return schema_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def describe_table(self, database_name: str, table_name: str, 
                      include_sample_data: bool = False) -> Dict[str, Any]:
        """Get detailed table information."""
        try:
            # PostgreSQL query to get column information
            columns_query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = %s
            ORDER BY ordinal_position
            """
            
            results = self.db.sql_get(columns_query.replace('%s', f"'{table_name}'"))
            
            columns = []
            for row in results:
                col_info = {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"]
                }
                if row["character_maximum_length"]:
                    col_info["max_length"] = row["character_maximum_length"]
                columns.append(col_info)
            
            result = {
                "table_name": table_name,
                "database": database_name,
                "columns": columns
            }
            
            # Get primary key information
            pk_query = """
            SELECT column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'public'
              AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            """
            pk_results = self.db.sql_get(pk_query.replace('%s', f"'{table_name}'"))
            primary_keys = [row["column_name"] for row in pk_results]
            
            # Mark primary key columns
            for col in result["columns"]:
                col["primary_key"] = col["name"] in primary_keys
            
            if include_sample_data:
                sample_data = self.sample_table(database_name, table_name, 5)
                result["sample_data"] = sample_data
                
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_table_relationships(self, database_name: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get foreign key relationships."""
        try:
            query = """
            SELECT
                tc.table_name as child_table,
                kcu.column_name as child_column,
                ccu.table_name as parent_table,
                ccu.column_name as parent_column,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_schema = 'public'
              AND tc.constraint_type = 'FOREIGN KEY'
            """
            
            if table_name:
                query += f" AND (tc.table_name = '{table_name}' OR ccu.table_name = '{table_name}')"
            
            results = self.db.sql_get(query)
            
            relationships = []
            for row in results:
                relationships.append({
                    "parent_table": row["parent_table"],
                    "parent_column": row["parent_column"],
                    "child_table": row["child_table"],
                    "child_column": row["child_column"],
                    "constraint_name": row["constraint_name"]
                })
            
            return relationships
            
        except Exception as e:
            return [{"error": str(e)}]
    
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
                sql_query = f"{sql_query.rstrip(';')} LIMIT {row_limit}"
            
            # Execute query
            start_time = datetime.now()
            results = self.db.sql_get(sql_query)
            end_time = datetime.now()
            
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
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
            dangerous_keywords = ["drop", "delete", "update", "insert", "truncate", "alter", "create"]
            for keyword in dangerous_keywords:
                if f" {keyword} " in f" {sql_lower} " or sql_lower.startswith(f"{keyword} "):
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
            # Note: AI_Query_History table doesn't exist in our test data yet
            # Return empty list for now
            return []
            
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
                columns_str = ", ".join([f'"{col}"' for col in columns])
            else:
                columns_str = "*"
                
            query = f'SELECT {columns_str} FROM "{table_name}" LIMIT {row_count}'
            results = self.db.sql_get(query)
            return results
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_column_stats(self, database_name: str, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get basic statistics for a column."""
        try:
            stats_query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT("{column_name}") as non_null_count,
                COUNT(*) - COUNT("{column_name}") as null_count,
                COUNT(DISTINCT "{column_name}") as unique_values
            FROM "{table_name}"
            """
            
            results = self.db.sql_get(stats_query)
            stats = results[0] if results else {}
            
            # Add column name and table info
            stats["column_name"] = column_name
            stats["table_name"] = table_name
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    # Memory Management Tools
    
    def store_memory(self, agent_name: str, memory_label: str, memory_content: str,
                    related_to_tags: str, purge_after: Optional[str] = None) -> Dict[str, Any]:
        """Store a memory for an agent."""
        try:
            # Convert purge_after string to timestamp if provided
            purge_timestamp = None
            if purge_after:
                try:
                    purge_timestamp = datetime.fromisoformat(purge_after.replace('Z', '+00:00'))
                except:
                    purge_timestamp = None
            
            memory_data = [{
                "Agent": agent_name,
                "Memory_label": memory_label,
                "Memory": memory_content,
                "Related_To": related_to_tags,
                "First_Posted": datetime.now(),
                "Times_Recalled": 0,
                "Purge_After": purge_timestamp
            }]
            
            self.db.sql_insert("ai_memories", memory_data)
            
            # Get the inserted memory ID
            last_id_query = """
            SELECT memory_id FROM ai_memories 
            WHERE agent = %s AND memory_label = %s 
            ORDER BY first_posted DESC LIMIT 1
            """
            id_results = self.db.sql_get(
                last_id_query.replace('%s', f"'{self.db.sql_escape(agent_name, False)}'")
                           .replace('%s', f"'{self.db.sql_escape(memory_label, False)}'")
            )
            
            memory_id = id_results[0]["memory_id"] if id_results else None
            
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
            if not tags:
                return []
            
            # Build LIKE conditions for each tag
            tag_conditions = []
            for tag in tags:
                escaped_tag = self.db.sql_escape(tag, False)
                tag_conditions.append(f"related_to ILIKE '%{escaped_tag}%'")
            
            query = f"""
            SELECT * FROM ai_memories 
            WHERE agent = '{self.db.sql_escape(agent_name, False)}' 
            AND ({' OR '.join(tag_conditions)})
            ORDER BY times_recalled DESC, last_recalled DESC
            LIMIT {limit}
            """
            
            memories = self.db.sql_get(query)
            
            # Update recall counts
            if memories:
                memory_ids = [str(memory["memory_id"]) for memory in memories]
                update_query = f"""
                UPDATE ai_memories 
                SET times_recalled = times_recalled + 1,
                    last_recalled = CURRENT_TIMESTAMP
                WHERE memory_id IN ({','.join(memory_ids)})
                """
                self.db.sql_run(update_query)
            
            return memories
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def search_memories(self, agent_name: str, search_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search through memory content."""
        try:
            escaped_search = self.db.sql_escape(search_text, False)
            escaped_agent = self.db.sql_escape(agent_name, False)
            
            query = f"""
            SELECT * FROM ai_memories 
            WHERE agent = '{escaped_agent}' 
            AND (memory ILIKE '%{escaped_search}%' OR memory_label ILIKE '%{escaped_search}%')
            ORDER BY times_recalled DESC
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
            update_parts = [f"memory = '{self.db.sql_escape(memory_content, False)}'"]
            
            if related_to_tags:
                update_parts.append(f"related_to = '{self.db.sql_escape(related_to_tags, False)}'")
            
            query = f"""
            UPDATE ai_memories 
            SET {', '.join(update_parts)}
            WHERE memory_id = {memory_id}
            """
            
            self.db.sql_run(query)
            
            return {"memory_id": memory_id, "updated": True}
            
        except Exception as e:
            return {"error": str(e)}
    
    def delete_memory(self, memory_id: int) -> Dict[str, Any]:
        """Delete a specific memory."""
        try:
            query = f"DELETE FROM ai_memories WHERE memory_id = {memory_id}"
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
                COALESCE(AVG(times_recalled), 0) as avg_recalls,
                COALESCE(MAX(times_recalled), 0) as max_recalls,
                COUNT(CASE WHEN times_recalled = 0 THEN 1 END) as unused_memories
            FROM ai_memories 
            WHERE agent = '{self.db.sql_escape(agent_name, False)}'
            """
            
            results = self.db.sql_get(stats_query)
            
            if results:
                stats = results[0]
                
                # Get most common tags
                tags_query = f"""
                SELECT related_to FROM ai_memories 
                WHERE agent = '{self.db.sql_escape(agent_name, False)}'
                  AND related_to IS NOT NULL AND related_to != ''
                """
                tag_results = self.db.sql_get(tags_query)
                
                # Simple tag frequency analysis
                tag_counts = {}
                for row in tag_results:
                    tags = str(row.get('related_to', '')).split()
                    for tag in tags:
                        if tag:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Get top 5 tags
                top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                
                stats['top_tags'] = top_tags
                return stats
            else:
                return {"total_memories": 0}
                
        except Exception as e:
            return {"error": str(e)}