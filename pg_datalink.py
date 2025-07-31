"""
PostgreSQL DataLink class for TriAI framework.
Provides database connectivity with error handling, connection management, and logging.
"""

import psycopg2
import psycopg2.extras
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Union, Optional


class PostgreSQLDataLink:
    """
    PostgreSQL database access layer with error handling, connection management, 
    and logging capabilities.
    """
    
    def __init__(self, connection_config: Dict[str, str], debug: bool = False):
        """
        Initialize PostgreSQL DataLink.
        
        Args:
            connection_config: Database connection configuration, e.g.:
                {
                    "host": "localhost",
                    "port": "5432",
                    "database": "triai_main",
                    "user": "triai_user",
                    "password": "secure_password"
                }
            debug: Enable debug logging
        """
        self.connection_config = connection_config
        self.debug = debug
        self.wasError = False
        self.connection = None
        self.log_entries = []
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def __del__(self):
        """Clean up database connection."""
        self._close_connection()
        
    def _close_connection(self):
        """Close the database connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                self.log(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None
        
    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get database connection with retry logic."""
        if self.connection and not self.connection.closed:
            try:
                # Test connection
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return self.connection
            except Exception:
                # Connection is dead, close it
                self._close_connection()
                
        # Create new connection with retry logic
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                conn_str = (
                    f"host={self.connection_config['host']} "
                    f"port={self.connection_config['port']} "
                    f"dbname={self.connection_config['database']} "
                    f"user={self.connection_config['user']} "
                    f"password={self.connection_config['password']}"
                )
                
                self.connection = psycopg2.connect(conn_str)
                self.connection.autocommit = True
                self.wasError = False
                return self.connection
                    
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
        Escape SQL strings for PostgreSQL.
        
        Args:
            data: Data to escape
            quote: Whether to add surrounding quotes
            
        Returns:
            Escaped string
        """
        if data is None:
            return "NULL"
            
        str_data = str(data)
        # PostgreSQL uses '' to escape single quotes
        escaped = str_data.replace("'", "''")
        
        if quote:
            return f"'{escaped}'"
        return escaped
        
    def sql_get(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return list of dictionaries.
        
        Args:
            sql: SQL SELECT statement
            
        Returns:
            List of dictionaries representing rows
        """
        try:
            self.wasError = False
            conn = self._get_connection()
            
            self.log(f"Executing query: {sql}")
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                
                # Convert RealDictRows to regular dictionaries
                result = []
                for row in rows:
                    result.append(dict(row))
                
                return result
            
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
        
    def sql_run(self, sql: str) -> None:
        """
        Execute SQL statement with no return value.
        
        Args:
            sql: SQL statement
        """
        try:
            self.wasError = False
            conn = self._get_connection()
            
            self.log(f"Executing statement: {sql}")
            
            with conn.cursor() as cursor:
                cursor.execute(sql)
            
        except Exception as e:
            self.wasError = True
            error_msg = f"SQL RUN Error: {str(e)} | SQL: {sql}"
            self.log(error_msg)
            raise Exception(error_msg)
            
    def sql_insert(self, table_name: str, data: Union[List[Dict[str, Any]], Dict[str, List[Any]]], 
                   chunk_size: int = 500, run: bool = True) -> Optional[str]:
        """
        Convert data to SQL insert statements in chunks.
        
        Args:
            table_name: Target table name
            data: Data as list of dictionaries or dictionary of lists
            chunk_size: Number of rows per chunk
            run: If False, returns SQL instead of executing
            
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
            
            # Build VALUES clauses using parameterized queries for safety
            placeholders = ", ".join(["%s"] * len(columns))
            values_clause = f"({placeholders})"
            
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES {values_clause}"
            all_sql.append((sql, chunk, columns))
            
        if not run:
            # Return a representation of the SQL
            return f"INSERT INTO {table_name} (...) VALUES (...) -- {len(data)} rows"
            
        # Execute the statements
        conn = self._get_connection()
        for sql, chunk, columns in all_sql:
            with conn.cursor() as cursor:
                # Use executemany for better performance
                values_list = []
                for row in chunk:
                    values = [row.get(col) for col in columns]
                    values_list.append(values)
                
                # For multiple rows, use VALUES with multiple value sets
                if len(values_list) > 1:
                    placeholders_multi = ", ".join([f"({', '.join(['%s'] * len(columns))})"] * len(values_list))
                    sql_multi = f"INSERT INTO {table_name} ({columns_str}) VALUES {placeholders_multi}"
                    
                    # Flatten the values list
                    flat_values = []
                    for values in values_list:
                        flat_values.extend(values)
                    
                    cursor.execute(sql_multi, flat_values)
                else:
                    cursor.execute(sql, values_list[0])
            
    def sql_upsert(self, table_name: str, data: Union[List[Dict[str, Any]], Dict[str, List[Any]]], 
                   key: List[str] = None, run: bool = True) -> Optional[str]:
        """
        Update if exists, otherwise insert (ON CONFLICT DO UPDATE for PostgreSQL).
        
        Args:
            table_name: Target table name
            data: Data as list of dictionaries or dictionary of lists
            key: Key columns for matching (if empty, uses all columns for matching)
            run: If False, returns SQL instead of executing
            
        Returns:
            SQL string if run=False, None otherwise
        """
        # Convert to list of dictionaries if needed
        if isinstance(data, dict):
            data = self.to_rows(data)
            
        if not data or not key:
            return self.sql_insert(table_name, data, run=run)
            
        all_sql = []
        
        for row in data:
            columns = list(row.keys())
            columns_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))
            
            # Build conflict columns
            conflict_columns = ", ".join(key)
            
            # Build update set clause (exclude key columns)
            update_columns = [col for col in columns if col not in key]
            update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])
            
            if update_set:
                sql = f"""
                INSERT INTO {table_name} ({columns_str}) 
                VALUES ({placeholders})
                ON CONFLICT ({conflict_columns}) 
                DO UPDATE SET {update_set}
                """
            else:
                sql = f"""
                INSERT INTO {table_name} ({columns_str}) 
                VALUES ({placeholders})
                ON CONFLICT ({conflict_columns}) 
                DO NOTHING
                """
            
            values = [row.get(col) for col in columns]
            all_sql.append((sql, values))
            
        if not run:
            return f"INSERT INTO {table_name} (...) VALUES (...) ON CONFLICT ... -- {len(data)} rows"
            
        # Execute the statements
        conn = self._get_connection()
        for sql, values in all_sql:
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
            
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
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            self.log(f"Connection test failed: {str(e)}")
            return False