"""
MockDataLink class that provides fake data for development and testing purposes.
Implements the same interface as DataLink but returns mock data instead of connecting to SQL Server.
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union, Optional


class MockDataLink:
    """
    Mock implementation of DataLink for development and testing.
    Provides fake data that matches the TriAI database schema.
    """
    
    def __init__(self, instances: List[Dict[str, str]], home_db: str = "", debug: bool = False):
        """
        Initialize MockDataLink with same signature as DataLink.
        
        Args:
            instances: Instance configurations (ignored in mock)
            home_db: Default database name (ignored in mock)
            debug: Enable debug logging
        """
        self.instances = instances
        self.home_db = home_db
        self.debug = debug
        self.wasError = False
        self.log_entries = []
        
        # Initialize mock data
        self._init_mock_data()
        
    def _init_mock_data(self):
        """Initialize mock database tables with sample data."""
        self.mock_tables = {
            'AI_Agents': [
                {
                    'Agent': 'DataAnalyst',
                    'Description': 'Analyzes data and generates reports',
                    'Model_API': 'ollama',
                    'Model': 'qwen2.5-coder',
                    'Model_API_KEY': None
                },
                {
                    'Agent': 'QueryBot',
                    'Description': 'Executes database queries and explains results',
                    'Model_API': 'openai',
                    'Model': 'gpt-4',
                    'Model_API_KEY': 'sk-mock-key-123'
                },
                {
                    'Agent': 'ReportGen',
                    'Description': 'Generates business reports from data',
                    'Model_API': 'anthropic',
                    'Model': 'claude-3-sonnet',
                    'Model_API_KEY': 'sk-ant-mock-key-456'
                }
            ],
            'AI_Messages': [
                {
                    'Message_ID': 1,
                    'Posted': datetime.now() - timedelta(hours=2),
                    'User_From': 'testuser',
                    'User_To': 'DataAnalyst',
                    'Message': 'Can you analyze the sales data for last quarter?',
                    'User_Read': datetime.now() - timedelta(hours=1, minutes=45)
                },
                {
                    'Message_ID': 2,
                    'Posted': datetime.now() - timedelta(hours=1, minutes=45),
                    'User_From': 'DataAnalyst',
                    'User_To': 'testuser',
                    'Message': 'I\'ll analyze the Q3 sales data for you. Let me query the database.',
                    'User_Read': None
                },
                {
                    'Message_ID': 3,
                    'Posted': datetime.now() - timedelta(minutes=30),
                    'User_From': 'testuser',
                    'User_To': 'QueryBot',
                    'Message': 'Show me all customers from California',
                    'User_Read': None
                }
            ],
            'AI_Memories': [
                {
                    'Memory_ID': 1,
                    'Agent': 'DataAnalyst',
                    'First_Posted': datetime.now() - timedelta(days=5),
                    'Times_Recalled': 3,
                    'Last_Recalled': datetime.now() - timedelta(hours=6),
                    'Memory_Label': 'Q3 Sales Analysis Method',
                    'Memory': 'User prefers quarterly sales analysis with trend comparison and regional breakdown.',
                    'Related_To': 'sales analysis quarterly trends',
                    'Purge_After': None
                },
                {
                    'Memory_ID': 2,
                    'Agent': 'QueryBot',
                    'First_Posted': datetime.now() - timedelta(days=2),
                    'Times_Recalled': 1,
                    'Last_Recalled': datetime.now() - timedelta(hours=12),
                    'Memory_Label': 'Customer Query Preferences',
                    'Memory': 'User often asks for customer data filtered by geographic regions.',
                    'Related_To': 'customers geography filters',
                    'Purge_After': None
                }
            ],
            'AI_Query_History': [
                {
                    'Query_ID': 1,
                    'Agent': 'DataAnalyst',
                    'Database_Name': 'SalesDB',
                    'SQL_Query': 'SELECT SUM(Amount) as Total_Sales, MONTH(OrderDate) as Month FROM Orders WHERE YEAR(OrderDate) = 2023 GROUP BY MONTH(OrderDate)',
                    'Executed_Time': datetime.now() - timedelta(hours=3),
                    'Row_Count': 12,
                    'Execution_Time_MS': 245
                },
                {
                    'Query_ID': 2,
                    'Agent': 'QueryBot',
                    'Database_Name': 'CustomerDB',
                    'SQL_Query': 'SELECT CustomerName, City, State FROM Customers WHERE State = \'CA\'',
                    'Executed_Time': datetime.now() - timedelta(minutes=45),
                    'Row_Count': 156,
                    'Execution_Time_MS': 89
                }
            ]
        }
        
        # Sample data for generic tables
        self.sample_customers = [
            {'CustomerID': 1, 'CustomerName': 'Acme Corp', 'City': 'Los Angeles', 'State': 'CA', 'Country': 'USA'},
            {'CustomerID': 2, 'CustomerName': 'TechStart Inc', 'City': 'San Francisco', 'State': 'CA', 'Country': 'USA'},
            {'CustomerID': 3, 'CustomerName': 'Global Solutions', 'City': 'New York', 'State': 'NY', 'Country': 'USA'},
            {'CustomerID': 4, 'CustomerName': 'Innovation Labs', 'City': 'Austin', 'State': 'TX', 'Country': 'USA'},
            {'CustomerID': 5, 'CustomerName': 'Pacific Ventures', 'City': 'Seattle', 'State': 'WA', 'Country': 'USA'}
        ]
        
        self.sample_sales = [
            {'OrderID': 1001, 'CustomerID': 1, 'OrderDate': datetime(2023, 10, 15), 'Amount': 15000.00},
            {'OrderID': 1002, 'CustomerID': 2, 'OrderDate': datetime(2023, 10, 18), 'Amount': 8750.50},
            {'OrderID': 1003, 'CustomerID': 3, 'OrderDate': datetime(2023, 10, 22), 'Amount': 22000.00},
            {'OrderID': 1004, 'CustomerID': 1, 'OrderDate': datetime(2023, 11, 5), 'Amount': 12500.00},
            {'OrderID': 1005, 'CustomerID': 4, 'OrderDate': datetime(2023, 11, 12), 'Amount': 18900.75}
        ]
        
    def __del__(self):
        """Clean up resources (no-op for mock)."""
        pass
        
    def sql_escape(self, data: Any, quote: bool = True) -> str:
        """Mock implementation of SQL escaping."""
        if data is None:
            return "NULL"
            
        str_data = str(data)
        escaped = str_data.replace("'", "''")
        
        if quote:
            return f"'{escaped}'"
        return escaped
        
    def sql_get(self, sql: str, database: str = "") -> List[Dict[str, Any]]:
        """
        Mock SQL SELECT execution that returns fake data based on query patterns.
        
        Args:
            sql: SQL SELECT statement
            database: Database name (ignored in mock)
            
        Returns:
            List of dictionaries representing mock rows
        """
        try:
            self.wasError = False
            self.log(f"Mock executing query: {sql}")
            
            sql_lower = sql.lower().strip()
            
            # Handle specific table queries
            if "ai_agents" in sql_lower:
                return self._filter_mock_data(self.mock_tables['AI_Agents'], sql)
            elif "ai_messages" in sql_lower:
                return self._filter_mock_data(self.mock_tables['AI_Messages'], sql)
            elif "ai_memories" in sql_lower:
                return self._filter_mock_data(self.mock_tables['AI_Memories'], sql)
            elif "ai_query_history" in sql_lower:
                return self._filter_mock_data(self.mock_tables['AI_Query_History'], sql)
            elif "customers" in sql_lower:
                return self._filter_mock_data(self.sample_customers, sql)
            elif "orders" in sql_lower or "sales" in sql_lower:
                return self._filter_mock_data(self.sample_sales, sql)
            elif "select 1" in sql_lower:
                return [{'result': 1}]
            elif "count(*)" in sql_lower:
                return [{'cnt': random.randint(0, 100)}]
            else:
                # Generic response for unknown queries
                return [
                    {'column1': 'Sample Value 1', 'column2': 123, 'column3': datetime.now()},
                    {'column1': 'Sample Value 2', 'column2': 456, 'column3': datetime.now() - timedelta(days=1)}
                ]
                
        except Exception as e:
            self.wasError = True
            error_msg = f"Mock SQL GET Error: {str(e)} | SQL: {sql}"
            self.log(error_msg)
            raise Exception(error_msg)
            
    def _filter_mock_data(self, data: List[Dict[str, Any]], sql: str) -> List[Dict[str, Any]]:
        """Apply basic filtering to mock data based on SQL WHERE clauses."""
        sql_lower = sql.lower()
        
        # Simple WHERE clause parsing for demonstration
        if "where" in sql_lower:
            # Look for common patterns
            if "state = 'ca'" in sql_lower or 'state = "ca"' in sql_lower:
                return [row for row in data if row.get('State') == 'CA']
            elif "agent =" in sql_lower:
                # Extract agent name (very basic parsing)
                parts = sql_lower.split("agent =")
                if len(parts) > 1:
                    agent_part = parts[1].strip()
                    agent_name = agent_part.split()[0].strip("'\"")
                    return [row for row in data if row.get('Agent', '').lower() == agent_name.lower()]
                    
        # Apply LIMIT if present
        if "limit" in sql_lower:
            try:
                limit_part = sql_lower.split("limit")[1].strip()
                limit_num = int(limit_part.split()[0])
                return data[:limit_num]
            except (IndexError, ValueError):
                pass
                
        return data
        
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
        Mock SQL execution with no return value.
        
        Args:
            sql: SQL statement
            database: Database name (ignored in mock)
        """
        try:
            self.wasError = False
            self.log(f"Mock executing statement: {sql}")
            
            sql_lower = sql.lower().strip()
            
            # Simulate different types of operations
            if sql_lower.startswith("insert"):
                self._simulate_insert(sql)
            elif sql_lower.startswith("update"):
                self._simulate_update(sql)
            elif sql_lower.startswith("delete"):
                self._simulate_delete(sql)
            elif sql_lower.startswith("create"):
                self.log("Mock: Table creation simulated")
            elif sql_lower.startswith("drop"):
                self.log("Mock: Table drop simulated")
            else:
                self.log("Mock: Generic SQL statement simulated")
                
            # Simulate execution time
            time.sleep(0.01)
            
        except Exception as e:
            self.wasError = True
            error_msg = f"Mock SQL RUN Error: {str(e)} | SQL: {sql}"
            self.log(error_msg)
            raise Exception(error_msg)
            
    def _simulate_insert(self, sql: str) -> None:
        """Simulate INSERT operations by updating mock tables."""
        sql_lower = sql.lower()
        
        if "ai_messages" in sql_lower:
            # Add to mock messages
            new_message = {
                'Message_ID': len(self.mock_tables['AI_Messages']) + 1,
                'Posted': datetime.now(),
                'User_From': 'mock_user',
                'User_To': 'mock_agent',
                'Message': 'Mock inserted message',
                'User_Read': None
            }
            self.mock_tables['AI_Messages'].append(new_message)
            
        elif "ai_memories" in sql_lower:
            # Add to mock memories
            new_memory = {
                'Memory_ID': len(self.mock_tables['AI_Memories']) + 1,
                'Agent': 'mock_agent',
                'First_Posted': datetime.now(),
                'Times_Recalled': 0,
                'Last_Recalled': None,
                'Memory_Label': 'Mock Memory',
                'Memory': 'Mock memory content',
                'Related_To': 'mock test',
                'Purge_After': None
            }
            self.mock_tables['AI_Memories'].append(new_memory)
            
        self.log(f"Mock: Simulated INSERT operation")
        
    def _simulate_update(self, sql: str) -> None:
        """Simulate UPDATE operations."""
        self.log(f"Mock: Simulated UPDATE operation")
        
    def _simulate_delete(self, sql: str) -> None:
        """Simulate DELETE operations.""" 
        self.log(f"Mock: Simulated DELETE operation")
        
    def sql_insert(self, table_name: str, data: Union[List[Dict[str, Any]], Dict[str, List[Any]]], 
                   chunk_size: int = 500, run: bool = True, database: str = "") -> Optional[str]:
        """
        Mock bulk insert operation.
        
        Args:
            table_name: Target table name
            data: Data as list of dictionaries or dictionary of lists
            chunk_size: Number of rows per chunk (ignored in mock)
            run: If False, returns SQL instead of executing
            database: Database name (ignored in mock)
            
        Returns:
            SQL string if run=False, None otherwise
        """
        # Convert to list of dictionaries if needed
        if isinstance(data, dict):
            data = self.to_rows(data)
            
        if not data:
            return None
            
        # Generate mock SQL
        columns = list(data[0].keys())
        mock_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES (mock_values)"
        
        if not run:
            return mock_sql
            
        # Simulate the insert
        self.log(f"Mock: Bulk inserted {len(data)} rows into {table_name}")
        if table_name.lower() == "ai_messages":
            self.mock_tables['AI_Messages'].extend(data[:5])  # Add first 5 for demo
            
    def sql_upsert(self, table_name: str, data: Union[List[Dict[str, Any]], Dict[str, List[Any]]], 
                   key: List[str] = None, run: bool = True, database: str = "") -> Optional[str]:
        """
        Mock upsert operation.
        
        Args:
            table_name: Target table name
            data: Data as list of dictionaries or dictionary of lists
            key: Key columns for matching
            run: If False, returns SQL instead of executing
            database: Database name (ignored in mock)
            
        Returns:
            SQL string if run=False, None otherwise
        """
        # Convert to list of dictionaries if needed
        if isinstance(data, dict):
            data = self.to_rows(data)
            
        if not data:
            return None
            
        mock_sql = f"-- Mock UPSERT for {table_name} with {len(data)} rows"
        
        if not run:
            return mock_sql
            
        self.log(f"Mock: Upserted {len(data)} rows in {table_name}")
        
    def log(self, message: str) -> None:
        """Save message to mock application log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[MOCK {timestamp}] {message}"
        
        self.log_entries.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.log_entries) > 1000:
            self.log_entries = self.log_entries[-1000:]
            
        # Print to console if debug mode
        if self.debug:
            print(log_entry)
            
    def read_log(self, num: int) -> List[str]:
        """
        Return last num entries in log.
        
        Args:
            num: Number of entries to return
            
        Returns:
            List of log entries
        """
        return self.log_entries[-num:] if num > 0 else []