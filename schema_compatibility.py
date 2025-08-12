"""
Schema compatibility layer for TriAI framework.
Handles differences between Mock, PostgreSQL, and SQL Server schemas.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class SchemaCompatibility:
    """
    Handles schema differences between database types.
    Provides field mapping and data conversion.
    """
    
    def __init__(self, database_type: str):
        """
        Initialize schema compatibility for a database type.
        
        Args:
            database_type: 'mock', 'postgresql', or 'sqlserver'
        """
        self.database_type = database_type.lower()
        
        # Field mappings from common names to database-specific names
        self.field_mappings = {
            'mock': {
                'ai_agents': {
                    'agent': 'Agent',
                    'description': 'Description', 
                    'role': 'Role',  # New field
                    'model_api': 'Model_API',
                    'model': 'Model',
                    'polling_interval': 'Polling_Interval',  # New field
                    'model_api_key': 'Model_API_KEY'  # Deprecated but kept for compatibility
                },
                'ai_messages': {
                    'message_id': 'Message_ID',
                    'posted': 'Posted',
                    'user_from': 'User_From', 
                    'user_to': 'User_To',
                    'message': 'Message',
                    'user_read': 'User_Read'
                },
                'ai_memories': {
                    'memory_id': 'Memory_ID',
                    'agent': 'Agent',
                    'first_posted': 'First_Posted',
                    'times_recalled': 'Times_Recalled',
                    'last_recalled': 'Last_Recalled',
                    'memory_label': 'Memory_Label',
                    'memory': 'Memory',
                    'related_to': 'Related_To',
                    'purge_after': 'Purge_After'
                },
                'ai_scripts': {
                    'language': 'Language',
                    'folder': 'Folder',
                    'filename': 'FileName',
                    'summary': 'Summary',
                    'script': 'Script'
                }
            },
            'postgresql': {
                'ai_agents': {
                    'agent': 'agent',
                    'description': 'description',
                    'role': 'role',
                    'model_api': 'model_api',
                    'model': 'model',
                    'polling_interval': 'polling_interval'
                },
                'ai_messages': {
                    'message_id': 'message_id',
                    'posted': 'posted',
                    'user_from': 'user_from',
                    'user_to': 'user_to', 
                    'message': 'message',
                    'user_read': 'user_read'
                },
                'ai_memories': {
                    'memory_id': 'memory_id',
                    'agent': 'agent',
                    'first_posted': 'first_posted',
                    'times_recalled': 'times_recalled',
                    'last_recalled': 'last_recalled',
                    'memory_label': 'memory_label',
                    'memory': 'memory',
                    'related_to': 'related_to',
                    'purge_after': 'purge_after'
                },
                'ai_scripts': {
                    'language': 'language',
                    'folder': 'folder',
                    'filename': 'filename',
                    'summary': 'summary',
                    'script': 'script'
                }
            },
            'sqlserver': {
                'ai_agents': {
                    'agent': 'Agent',
                    'description': 'Description',
                    'role': 'Role',
                    'model_api': 'Model_API',
                    'model': 'Model', 
                    'polling_interval': 'Polling_Interval'
                },
                'ai_messages': {
                    'message_id': 'Message_ID',
                    'posted': 'Posted',
                    'user_from': 'User_From',
                    'user_to': 'User_To',
                    'message': 'Message',
                    'user_read': 'User_Read'
                },
                'ai_memories': {
                    'memory_id': 'Memory_ID',
                    'agent': 'Agent',
                    'first_posted': 'First_Posted',
                    'times_recalled': 'Times_Recalled',
                    'last_recalled': 'Last_Recalled',
                    'memory_label': 'Memory_Label',
                    'memory': 'Memory',
                    'related_to': 'Related_To',
                    'purge_after': 'Purge_After'
                },
                'ai_scripts': {
                    'language': 'Language',
                    'folder': 'Folder',
                    'filename': 'FileName',
                    'summary': 'Summary',
                    'script': 'Script'
                }
            }
        }
        
        # Table name mappings
        self.table_mappings = {
            'mock': {
                'ai_agents': 'AI_Agents',
                'ai_messages': 'AI_Messages', 
                'ai_memories': 'AI_Memories',
                'ai_scripts': 'AI_Scripts'
            },
            'postgresql': {
                'ai_agents': 'ai_agents',
                'ai_messages': 'ai_messages',
                'ai_memories': 'ai_memories', 
                'ai_scripts': 'ai_scripts'
            },
            'sqlserver': {
                'ai_agents': 'AI_Agents',
                'ai_messages': 'AI_Messages',
                'ai_memories': 'AI_Memories',
                'ai_scripts': 'AI_Scripts'
            }
        }
    
    def get_table_name(self, logical_table: str) -> str:
        """
        Get the physical table name for the current database type.
        
        Args:
            logical_table: Logical table name (ai_agents, ai_messages, etc.)
            
        Returns:
            Physical table name for the database type
        """
        return self.table_mappings[self.database_type].get(logical_table, logical_table)
    
    def get_field_name(self, table: str, logical_field: str) -> str:
        """
        Get the physical field name for the current database type.
        
        Args:
            table: Logical table name
            logical_field: Logical field name
            
        Returns:
            Physical field name for the database type
        """
        table_mapping = self.field_mappings[self.database_type].get(table, {})
        return table_mapping.get(logical_field, logical_field)
    
    def convert_row_to_standard(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a database row to standard field names.
        
        Args:
            table: Table name
            row: Row data from database
            
        Returns:
            Row with standard field names
        """
        if not row:
            return row
            
        table_mapping = self.field_mappings[self.database_type].get(table, {})
        
        # Create reverse mapping (physical -> logical)
        reverse_mapping = {v: k for k, v in table_mapping.items()}
        
        converted = {}
        for key, value in row.items():
            # Convert to logical name if mapping exists, otherwise keep original
            logical_name = reverse_mapping.get(key, key.lower())
            converted[logical_name] = value
            
        return converted
    
    def convert_rows_to_standard(self, table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert multiple rows to standard field names."""
        return [self.convert_row_to_standard(table, row) for row in rows]
    
    def convert_row_from_standard(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a standard row to database-specific field names.
        
        Args:
            table: Table name
            row: Row data with standard field names
            
        Returns:
            Row with database-specific field names
        """
        if not row:
            return row
            
        table_mapping = self.field_mappings[self.database_type].get(table, {})
        
        converted = {}
        for key, value in row.items():
            # Convert to physical name if mapping exists, otherwise keep original
            physical_name = table_mapping.get(key, key)
            converted[physical_name] = value
            
        return converted
    
    def convert_rows_from_standard(self, table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert multiple rows from standard field names."""
        return [self.convert_row_from_standard(table, row) for row in rows]
    
    def build_select_query(self, table: str, fields: Optional[List[str]] = None, 
                          where_clause: str = "", order_by: str = "", limit: int = 0) -> str:
        """
        Build a SELECT query with proper table and field names for the database type.
        
        Args:
            table: Logical table name
            fields: List of logical field names (None for all fields)
            where_clause: WHERE clause (already with proper field names)
            order_by: ORDER BY clause
            limit: Row limit
            
        Returns:
            Complete SELECT query for the database type
        """
        physical_table = self.get_table_name(table)
        
        if fields:
            # Convert field names to physical names
            physical_fields = []
            for field in fields:
                physical_field = self.get_field_name(table, field)
                physical_fields.append(physical_field)
            fields_str = ", ".join(physical_fields)
        else:
            fields_str = "*"
        
        query = f"SELECT {fields_str} FROM {physical_table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
            
        if order_by:
            query += f" ORDER BY {order_by}"
            
        if limit > 0:
            if self.database_type == 'postgresql':
                query += f" LIMIT {limit}"
            elif self.database_type == 'sqlserver':
                # SQL Server uses TOP
                query = query.replace(f"SELECT {fields_str}", f"SELECT TOP {limit} {fields_str}")
            else:  # mock
                query += f" LIMIT {limit}"
        
        return query
    
    def build_insert_query(self, table: str, data: List[Dict[str, Any]]) -> str:
        """
        Build an INSERT query with proper table and field names.
        
        Args:
            table: Logical table name
            data: List of rows with standard field names
            
        Returns:
            INSERT query for the database type
        """
        if not data:
            return ""
            
        physical_table = self.get_table_name(table)
        
        # Convert first row to get field names
        sample_row = self.convert_row_from_standard(table, data[0])
        columns = list(sample_row.keys())
        
        query = f"INSERT INTO {physical_table} ({', '.join(columns)}) VALUES "
        
        # Add placeholder values
        if self.database_type == 'postgresql':
            placeholders = ", ".join(["%s"] * len(columns))
        else:  # sqlserver and mock
            placeholders = ", ".join(["?"] * len(columns))
            
        query += f"({placeholders})"
        
        return query
    
    def get_agent_schema_differences(self) -> Dict[str, Any]:
        """
        Get information about schema differences across database types.
        
        Returns:
            Dictionary describing schema differences
        """
        return {
            "new_fields_added": ["role", "polling_interval"],
            "deprecated_fields": ["model_api_key"],
            "field_name_case_differences": {
                "postgresql": "lowercase", 
                "sqlserver": "PascalCase",
                "mock": "PascalCase"
            },
            "compatibility_notes": [
                "Role field added to store agent system prompts",
                "Polling_Interval added for customizable polling timing",
                "Model_API_KEY field deprecated for security",
                "PostgreSQL uses lowercase field names",
                "SQL Server and Mock use PascalCase field names"
            ]
        }

# Global compatibility instance
_compatibility_instance = None

def get_schema_compatibility(database_type: str) -> SchemaCompatibility:
    """Get singleton schema compatibility instance."""
    global _compatibility_instance
    if _compatibility_instance is None or _compatibility_instance.database_type != database_type.lower():
        _compatibility_instance = SchemaCompatibility(database_type)
    return _compatibility_instance