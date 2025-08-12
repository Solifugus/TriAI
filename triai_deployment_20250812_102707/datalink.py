"""
DataLink class for SQL Server database connectivity with error handling and retry logic.
"""

import pyodbc
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Union, Optional


class DataLink:
    """
    Centralized database access layer with error handling, connection management, 
    and logging capabilities for SQL Server.
    """
    
    def __init__(self, instances: List[Dict[str, str]], home_db: str = "", debug: bool = False):
        """
        Initialize DataLink with SQL Server instance configurations.
        
        Args:
            instances: List of instance configurations, e.g.:
                [
                    {
                        "instance": "myserver\\myinstance",
                        "user": "secret", 
                        "password": "secret"
                    }
                ]
            home_db: Default database name
            debug: Enable debug logging
        """
        self.instances = instances
        self.home_db = home_db
        self.debug = debug
        self.wasError = False
        self.connections = {}
        self.log_entries = []
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def __del__(self):
        """Clean up database connections."""
        self._close_all_connections()
        
    def _close_all_connections(self):
        """Close all open connections."""
        for conn in self.connections.values():
            try:
                if conn:
                    conn.close()
            except Exception as e:
                self.log(f"Error closing connection: {str(e)}")
        self.connections.clear()
        
    def _get_connection_string(self, instance_config: Dict[str, str], database: str = "") -> str:
        """Build SQL Server connection string."""
        server = instance_config["instance"]
        user = instance_config["user"]
        password = instance_config["password"]
        
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
        conn_str += f"UID={user};PWD={password};"
        
        if database:
            conn_str += f"DATABASE={database};"
        elif self.home_db:
            conn_str += f"DATABASE={self.home_db};"
            
        conn_str += "TrustServerCertificate=yes;"
        
        return conn_str
        
    def _get_connection(self, database: str = "") -> pyodbc.Connection:
        """Get database connection with retry logic."""
        db_key = database or self.home_db
        
        if db_key in self.connections and self.connections[db_key]:
            try:
                # Test connection
                cursor = self.connections[db_key].cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return self.connections[db_key]
            except Exception:
                # Connection is dead, remove it
                self.connections[db_key] = None
                
        # Create new connection with retry logic
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                for instance in self.instances:
                    conn_str = self._get_connection_string(instance, database)
                    conn = pyodbc.connect(conn_str, timeout=30)
                    conn.autocommit = True
                    self.connections[db_key] = conn
                    self.wasError = False
                    return conn
                    
            except Exception as e:
                self.wasError = True
                error_msg = f"Connection attempt {attempt + 1} failed: {str(e)}"
                self.log(error_msg)
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise Exception(f"Failed to connect after {max_retries} attempts: {str(e)}")
                    
    def sql_escape(self, data: Any, quote: bool = True) -> str:
        """
        Escape SQL strings by replacing single quotes with double quotes.
        
        Args:
            data: Data to escape
            quote: Whether to add surrounding quotes
            
        Returns:
            Escaped string
        """
        if data is None:
            return "NULL"
            
        str_data = str(data)
        escaped = str_data.replace("'", "''")
        
        if quote:
            return f"'{escaped}'"
        return escaped
        
    def sql_get(self, sql: str, database: str = "") -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return list of dictionaries.
        
        Args:
            sql: SQL SELECT statement
            database: Database name (optional)
            
        Returns:
            List of dictionaries representing rows
        """
        try:
            self.wasError = False
            conn = self._get_connection(database)
            cursor = conn.cursor()
            
            self.log(f"Executing query: {sql}")
            cursor.execute(sql)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows and convert to dictionaries
            rows = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value
                rows.append(row_dict)
                
            cursor.close()
            return rows
            
        except Exception as e:
            self.wasError = True
            error_msg = f"SQL GET Error: {str(e)} | SQL: {sql}"
            self.log(error_msg)
            raise Exception(error_msg)
            
    def to_columns(self, list_of_dict: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """Convert list of dictionaries to dictionary of lists."""
        if not list_of_dict:
            return {}
            
        result = {}
        for key in list_of_dict[0].keys():
            result[key] = [row.get(key) for row in list_of_dict]
        return result
        
    def to_rows(self, dict_of_list: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Convert dictionary of lists to list of dictionaries."""
        if not dict_of_list:
            return []
            
        keys = list(dict_of_list.keys())
        if not keys:
            return []
            
        num_rows = len(dict_of_list[keys[0]])
        result = []
        
        for i in range(num_rows):
            row = {}
            for key in keys:
                row[key] = dict_of_list[key][i] if i < len(dict_of_list[key]) else None
            result.append(row)
            
        return result
        
    def sql_run(self, sql: str, database: str = "") -> None:
        """
        Execute SQL statement with no return value.
        
        Args:
            sql: SQL statement
            database: Database name (optional)
        """
        try:
            self.wasError = False
            conn = self._get_connection(database)
            cursor = conn.cursor()
            
            self.log(f"Executing statement: {sql}")
            cursor.execute(sql)
            cursor.close()
            
        except Exception as e:
            self.wasError = True
            error_msg = f"SQL RUN Error: {str(e)} | SQL: {sql}"
            self.log(error_msg)
            raise Exception(error_msg)
            
    def sql_insert(self, table_name: str, data: Union[List[Dict[str, Any]], Dict[str, List[Any]]], 
                   chunk_size: int = 500, run: bool = True, database: str = "") -> Optional[str]:
        """
        Convert data to SQL insert statements in chunks.
        
        Args:
            table_name: Target table name
            data: Data as list of dictionaries or dictionary of lists
            chunk_size: Number of rows per chunk
            run: If False, returns SQL instead of executing
            database: Database name (optional)
            
        Returns:
            SQL string if run=False, None otherwise
        """
        # Convert to list of dictionaries if needed
        if isinstance(data, dict):
            data = self.to_rows(data)
            
        if not data:
            return None
            
        # Build INSERT statements in chunks
        all_sql = []
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            
            # Get column names from first row
            columns = list(chunk[0].keys())
            columns_str = ", ".join(columns)
            
            # Build VALUES clauses
            values_clauses = []
            for row in chunk:
                values = []
                for col in columns:
                    value = row.get(col)
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, (int, float)):
                        values.append(str(value))
                    else:
                        values.append(self.sql_escape(value))
                values_clauses.append(f"({', '.join(values)})")
                
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES {', '.join(values_clauses)}"
            all_sql.append(sql)
            
        combined_sql = ";\n".join(all_sql)
        
        if not run:
            return combined_sql
            
        # Execute the statements
        for sql in all_sql:
            self.sql_run(sql, database)
            
    def sql_upsert(self, table_name: str, data: Union[List[Dict[str, Any]], Dict[str, List[Any]]], 
                   key: List[str] = None, run: bool = True, database: str = "") -> Optional[str]:
        """
        Update if exists, otherwise insert (MERGE operation).
        
        Args:
            table_name: Target table name
            data: Data as list of dictionaries or dictionary of lists
            key: Key columns for matching (if empty, uses all columns for matching)
            run: If False, returns SQL instead of executing
            database: Database name (optional)
            
        Returns:
            SQL string if run=False, None otherwise
        """
        # Convert to list of dictionaries if needed
        if isinstance(data, dict):
            data = self.to_rows(data)
            
        if not data or not key:
            return self.sql_insert(table_name, data, run=run, database=database)
            
        # For simplicity, implement as separate UPDATE/INSERT operations
        # In production, you might want to use SQL Server's MERGE statement
        all_sql = []
        
        for row in data:
            # Build WHERE clause for key matching
            where_conditions = []
            for key_col in key:
                value = row.get(key_col)
                if value is None:
                    where_conditions.append(f"{key_col} IS NULL")
                elif isinstance(value, (int, float)):
                    where_conditions.append(f"{key_col} = {value}")
                else:
                    where_conditions.append(f"{key_col} = {self.sql_escape(value)}")
            where_clause = " AND ".join(where_conditions)
            
            # Check if record exists
            check_sql = f"SELECT COUNT(*) as cnt FROM {table_name} WHERE {where_clause}"
            
            # Build UPDATE statement
            set_clauses = []
            for col, value in row.items():
                if col not in key:  # Don't update key columns
                    if value is None:
                        set_clauses.append(f"{col} = NULL")
                    elif isinstance(value, (int, float)):
                        set_clauses.append(f"{col} = {value}")
                    else:
                        set_clauses.append(f"{col} = {self.sql_escape(value)}")
            
            if set_clauses:
                update_sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
            else:
                update_sql = None
                
            # Build INSERT statement
            columns = list(row.keys())
            values = []
            for col in columns:
                value = row.get(col)
                if value is None:
                    values.append("NULL")
                elif isinstance(value, (int, float)):
                    values.append(str(value))
                else:
                    values.append(self.sql_escape(value))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)})"
            
            # Combine into conditional logic
            if update_sql:
                upsert_sql = f"""
IF EXISTS (SELECT 1 FROM {table_name} WHERE {where_clause})
    {update_sql}
ELSE
    {insert_sql}
"""
            else:
                upsert_sql = f"""
IF NOT EXISTS (SELECT 1 FROM {table_name} WHERE {where_clause})
    {insert_sql}
"""
            all_sql.append(upsert_sql.strip())
            
        combined_sql = ";\n".join(all_sql)
        
        if not run:
            return combined_sql
            
        # Execute the statements
        for sql in all_sql:
            self.sql_run(sql, database)
            
    def log(self, message: str) -> None:
        """Save message to application log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_entries.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.log_entries) > 1000:
            self.log_entries = self.log_entries[-1000:]
            
        # Also log to Python logger
        if self.wasError:
            self.logger.error(log_entry)
        else:
            self.logger.info(log_entry)
            
    def read_log(self, num: int) -> List[str]:
        """
        Return last num entries in log.
        
        Args:
            num: Number of entries to return
            
        Returns:
            List of log entries
        """
        return self.log_entries[-num:] if num > 0 else []