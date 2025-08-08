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
        """Initialize mock database tables with credit union sample data."""
        self.mock_tables = {
            'AI_Agents': [
                {
                    'Agent': 'LoanAnalyst',
                    'Description': 'Analyzes loan portfolios, risk assessment, and member lending patterns',
                    'Model_API': 'ollama',
                    'Model': 'qwen2.5-coder',
                    'Model_API_KEY': None
                },
                {
                    'Agent': 'MemberServices',
                    'Description': 'Provides insights on member accounts, transactions, and service usage',
                    'Model_API': 'ollama',
                    'Model': 'qwen2.5-coder',
                    'Model_API_KEY': None
                },
                {
                    'Agent': 'ComplianceBot',
                    'Description': 'Monitors regulatory compliance, audit trails, and risk management',
                    'Model_API': 'anthropic',
                    'Model': 'claude-3-sonnet',
                    'Model_API_KEY': 'sk-ant-mock-key-456'
                },
                {
                    'Agent': 'FinancialReporter',
                    'Description': 'Generates financial reports, dashboards, and member analytics',
                    'Model_API': 'openai',
                    'Model': 'gpt-4',
                    'Model_API_KEY': 'sk-mock-key-123'
                }
            ],
            'AI_Messages': [
                {
                    'Message_ID': 1,
                    'Posted': datetime.now() - timedelta(hours=3),
                    'User_From': 'creditmanager',
                    'User_To': 'LoanAnalyst',
                    'Message': 'Can you analyze our auto loan portfolio performance for Q4?',
                    'User_Read': datetime.now() - timedelta(hours=2, minutes=45)
                },
                {
                    'Message_ID': 2,
                    'Posted': datetime.now() - timedelta(hours=2, minutes=45),
                    'User_From': 'LoanAnalyst',
                    'User_To': 'creditmanager',
                    'Message': 'Analyzing Q4 auto loans... Portfolio shows 2.1% delinquency rate, avg loan $28,500, 4.2% APR average.',
                    'User_Read': datetime.now() - timedelta(hours=2, minutes=30)
                },
                {
                    'Message_ID': 3,
                    'Posted': datetime.now() - timedelta(hours=1, minutes=30),
                    'User_From': 'branchmanager',
                    'User_To': 'MemberServices',
                    'Message': 'Show me member account growth trends for our three branches',
                    'User_Read': None
                },
                {
                    'Message_ID': 4,
                    'Posted': datetime.now() - timedelta(hours=1, minutes=15),
                    'User_From': 'MemberServices',
                    'User_To': 'branchmanager',
                    'Message': 'Branch A: +127 members, Branch B: +89 members, Branch C: +156 members. Total assets grew 8.3%.',
                    'User_Read': None
                },
                {
                    'Message_ID': 5,
                    'Posted': datetime.now() - timedelta(minutes=45),
                    'User_From': 'auditteam',
                    'User_To': 'ComplianceBot',
                    'Message': 'Check BSA compliance for large cash transactions this month',
                    'User_Read': None
                },
                {
                    'Message_ID': 6,
                    'Posted': datetime.now() - timedelta(minutes=20),
                    'User_From': 'president',
                    'User_To': 'FinancialReporter',
                    'Message': 'Generate the monthly board report with key metrics and trends',
                    'User_Read': None
                }
            ],
            'AI_Memories': [
                {
                    'Memory_ID': 1,
                    'Agent': 'LoanAnalyst',
                    'First_Posted': datetime.now() - timedelta(days=7),
                    'Times_Recalled': 5,
                    'Last_Recalled': datetime.now() - timedelta(hours=2),
                    'Memory_Label': 'Auto Loan Risk Preferences',
                    'Memory': 'Credit manager prefers auto loan analysis with delinquency rates, average loan amounts, and APR trends by month.',
                    'Related_To': 'auto loans risk delinquency apr analysis',
                    'Purge_After': None
                },
                {
                    'Memory_ID': 2,
                    'Agent': 'MemberServices',
                    'First_Posted': datetime.now() - timedelta(days=4),
                    'Times_Recalled': 3,
                    'Last_Recalled': datetime.now() - timedelta(hours=1, minutes=30),
                    'Memory_Label': 'Branch Performance Metrics',
                    'Memory': 'Branch managers frequently request member growth, asset growth, and new account metrics by branch location.',
                    'Related_To': 'branches members growth assets accounts',
                    'Purge_After': None
                },
                {
                    'Memory_ID': 3,
                    'Agent': 'ComplianceBot',
                    'First_Posted': datetime.now() - timedelta(days=10),
                    'Times_Recalled': 8,
                    'Last_Recalled': datetime.now() - timedelta(days=1),
                    'Memory_Label': 'BSA Monitoring Patterns',
                    'Memory': 'Audit team regularly monitors large cash transactions above $10K for BSA compliance and suspicious activity.',
                    'Related_To': 'bsa compliance cash transactions suspicious activity',
                    'Purge_After': None
                },
                {
                    'Memory_ID': 4,
                    'Agent': 'FinancialReporter',
                    'First_Posted': datetime.now() - timedelta(days=15),
                    'Times_Recalled': 12,
                    'Last_Recalled': datetime.now() - timedelta(days=2),
                    'Memory_Label': 'Board Report Requirements',
                    'Memory': 'Monthly board reports require: asset growth, member growth, loan portfolio health, profitability metrics, and regulatory compliance status.',
                    'Related_To': 'board reports monthly assets members loans profitability compliance',
                    'Purge_After': None
                },
                {
                    'Memory_ID': 5,
                    'Agent': 'LoanAnalyst',
                    'First_Posted': datetime.now() - timedelta(days=3),
                    'Times_Recalled': 2,
                    'Last_Recalled': datetime.now() - timedelta(hours=8),
                    'Memory_Label': 'Mortgage Underwriting Criteria',
                    'Memory': 'Current mortgage underwriting focuses on debt-to-income ratios below 43%, credit scores above 620, and loan-to-value under 95%.',
                    'Related_To': 'mortgage underwriting dti credit score ltv',
                    'Purge_After': None
                }
            ],
            'AI_Query_History': [
                {
                    'Query_ID': 1,
                    'Agent': 'LoanAnalyst',
                    'Database_Name': 'LoanDB',
                    'SQL_Query': 'SELECT COUNT(*) as Total_Loans, AVG(Loan_Amount) as Avg_Amount, AVG(Interest_Rate) as Avg_Rate FROM Auto_Loans WHERE YEAR(Origination_Date) = 2024',
                    'Executed_Time': datetime.now() - timedelta(hours=2, minutes=45),
                    'Row_Count': 1,
                    'Execution_Time_MS': 156
                },
                {
                    'Query_ID': 2,
                    'Agent': 'MemberServices',
                    'Database_Name': 'MemberDB',
                    'SQL_Query': 'SELECT Branch_ID, COUNT(*) as New_Members FROM Members WHERE Join_Date >= DATEADD(month, -1, GETDATE()) GROUP BY Branch_ID',
                    'Executed_Time': datetime.now() - timedelta(hours=1, minutes=15),
                    'Row_Count': 3,
                    'Execution_Time_MS': 234
                },
                {
                    'Query_ID': 3,
                    'Agent': 'ComplianceBot',
                    'Database_Name': 'TransactionDB',
                    'SQL_Query': 'SELECT COUNT(*) as Large_Cash_Transactions FROM Transactions WHERE Transaction_Type = \'CASH\' AND Amount > 10000 AND Transaction_Date >= DATEADD(month, -1, GETDATE())',
                    'Executed_Time': datetime.now() - timedelta(minutes=45),
                    'Row_Count': 1,
                    'Execution_Time_MS': 298
                },
                {
                    'Query_ID': 4,
                    'Agent': 'FinancialReporter',
                    'Database_Name': 'FinancialDB',
                    'SQL_Query': 'SELECT SUM(Assets) as Total_Assets, SUM(Loans_Outstanding) as Total_Loans, COUNT(DISTINCT Member_ID) as Total_Members FROM Monthly_Financials WHERE Report_Month = DATEADD(month, -1, GETDATE())',
                    'Executed_Time': datetime.now() - timedelta(minutes=20),
                    'Row_Count': 1,
                    'Execution_Time_MS': 445
                },
                {
                    'Query_ID': 5,
                    'Agent': 'LoanAnalyst',
                    'Database_Name': 'LoanDB',
                    'SQL_Query': 'SELECT Loan_Type, COUNT(*) as Count, AVG(Credit_Score) as Avg_Credit_Score FROM Loans WHERE Status = \'DELINQUENT\' GROUP BY Loan_Type',
                    'Executed_Time': datetime.now() - timedelta(days=1, hours=3),
                    'Row_Count': 4,
                    'Execution_Time_MS': 678
                },
                {
                    'Query_ID': 6,
                    'Agent': 'MemberServices',
                    'Database_Name': 'AccountDB',
                    'SQL_Query': 'SELECT Account_Type, AVG(Balance) as Avg_Balance, COUNT(*) as Account_Count FROM Accounts WHERE Status = \'ACTIVE\' GROUP BY Account_Type',
                    'Executed_Time': datetime.now() - timedelta(days=2),
                    'Row_Count': 5,
                    'Execution_Time_MS': 123
                }
            ]
        }
        
        # Sample data for credit union tables
        self.sample_members = [
            {'Member_ID': 100001, 'First_Name': 'Sarah', 'Last_Name': 'Johnson', 'Email': 'sarah.j@email.com', 'Phone': '555-0101', 'Address': '123 Oak St', 'City': 'Portland', 'State': 'OR', 'ZIP': '97201', 'Join_Date': datetime(2020, 3, 15), 'Status': 'ACTIVE', 'Branch_ID': 1, 'Credit_Score': 745},
            {'Member_ID': 100002, 'First_Name': 'Michael', 'Last_Name': 'Chen', 'Email': 'm.chen@email.com', 'Phone': '555-0102', 'Address': '456 Pine Ave', 'City': 'Portland', 'State': 'OR', 'ZIP': '97202', 'Join_Date': datetime(2019, 7, 22), 'Status': 'ACTIVE', 'Branch_ID': 1, 'Credit_Score': 689},
            {'Member_ID': 100003, 'First_Name': 'Emily', 'Last_Name': 'Davis', 'Email': 'emily.davis@email.com', 'Phone': '555-0103', 'Address': '789 Elm Dr', 'City': 'Beaverton', 'State': 'OR', 'ZIP': '97005', 'Join_Date': datetime(2021, 1, 8), 'Status': 'ACTIVE', 'Branch_ID': 2, 'Credit_Score': 712},
            {'Member_ID': 100004, 'First_Name': 'Robert', 'Last_Name': 'Wilson', 'Email': 'r.wilson@email.com', 'Phone': '555-0104', 'Address': '321 Maple Ln', 'City': 'Tigard', 'State': 'OR', 'ZIP': '97223', 'Join_Date': datetime(2018, 11, 30), 'Status': 'ACTIVE', 'Branch_ID': 2, 'Credit_Score': 658},
            {'Member_ID': 100005, 'First_Name': 'Jessica', 'Last_Name': 'Martinez', 'Email': 'j.martinez@email.com', 'Phone': '555-0105', 'Address': '654 Cedar Ct', 'City': 'Gresham', 'State': 'OR', 'ZIP': '97030', 'Join_Date': datetime(2022, 5, 14), 'Status': 'ACTIVE', 'Branch_ID': 3, 'Credit_Score': 723},
            {'Member_ID': 100006, 'First_Name': 'David', 'Last_Name': 'Anderson', 'Email': 'd.anderson@email.com', 'Phone': '555-0106', 'Address': '987 Birch Way', 'City': 'Lake Oswego', 'State': 'OR', 'ZIP': '97034', 'Join_Date': datetime(2017, 9, 3), 'Status': 'ACTIVE', 'Branch_ID': 1, 'Credit_Score': 798},
            {'Member_ID': 100007, 'First_Name': 'Lisa', 'Last_Name': 'Thompson', 'Email': 'lisa.t@email.com', 'Phone': '555-0107', 'Address': '147 Spruce St', 'City': 'Milwaukie', 'State': 'OR', 'ZIP': '97222', 'Join_Date': datetime(2023, 2, 17), 'Status': 'ACTIVE', 'Branch_ID': 3, 'Credit_Score': 701},
            {'Member_ID': 100008, 'First_Name': 'James', 'Last_Name': 'Brown', 'Email': 'j.brown@email.com', 'Phone': '555-0108', 'Address': '258 Willow Ave', 'City': 'Oregon City', 'State': 'OR', 'ZIP': '97045', 'Join_Date': datetime(2021, 8, 25), 'Status': 'ACTIVE', 'Branch_ID': 2, 'Credit_Score': 675},
            {'Member_ID': 100009, 'First_Name': 'Amanda', 'Last_Name': 'Garcia', 'Email': 'a.garcia@email.com', 'Phone': '555-0109', 'Address': '369 Ash Blvd', 'City': 'Hillsboro', 'State': 'OR', 'ZIP': '97124', 'Join_Date': datetime(2020, 12, 11), 'Status': 'ACTIVE', 'Branch_ID': 1, 'Credit_Score': 734}
        ]
        
        self.sample_accounts = [
            {'Account_ID': 20001, 'Member_ID': 100001, 'Account_Type': 'CHECKING', 'Balance': 3245.67, 'Interest_Rate': 0.05, 'Open_Date': datetime(2020, 3, 16), 'Status': 'ACTIVE'},
            {'Account_ID': 20002, 'Member_ID': 100001, 'Account_Type': 'SAVINGS', 'Balance': 15780.23, 'Interest_Rate': 2.15, 'Open_Date': datetime(2020, 3, 16), 'Status': 'ACTIVE'},
            {'Account_ID': 20003, 'Member_ID': 100002, 'Account_Type': 'CHECKING', 'Balance': 1892.45, 'Interest_Rate': 0.05, 'Open_Date': datetime(2019, 7, 23), 'Status': 'ACTIVE'},
            {'Account_ID': 20004, 'Member_ID': 100002, 'Account_Type': 'MONEY_MARKET', 'Balance': 25000.00, 'Interest_Rate': 3.25, 'Open_Date': datetime(2021, 4, 10), 'Status': 'ACTIVE'},
            {'Account_ID': 20005, 'Member_ID': 100003, 'Account_Type': 'CHECKING', 'Balance': 2156.78, 'Interest_Rate': 0.05, 'Open_Date': datetime(2021, 1, 9), 'Status': 'ACTIVE'},
            {'Account_ID': 20006, 'Member_ID': 100003, 'Account_Type': 'SAVINGS', 'Balance': 8934.56, 'Interest_Rate': 2.15, 'Open_Date': datetime(2021, 1, 9), 'Status': 'ACTIVE'},
            {'Account_ID': 20007, 'Member_ID': 100004, 'Account_Type': 'CHECKING', 'Balance': 567.23, 'Interest_Rate': 0.05, 'Open_Date': datetime(2018, 12, 1), 'Status': 'ACTIVE'},
            {'Account_ID': 20008, 'Member_ID': 100005, 'Account_Type': 'CHECKING', 'Balance': 4123.89, 'Interest_Rate': 0.05, 'Open_Date': datetime(2022, 5, 15), 'Status': 'ACTIVE'},
            {'Account_ID': 20009, 'Member_ID': 100005, 'Account_Type': 'CD', 'Balance': 50000.00, 'Interest_Rate': 4.75, 'Open_Date': datetime(2023, 1, 1), 'Status': 'ACTIVE'}
        ]
        
        self.sample_loans = [
            {'Loan_ID': 30001, 'Member_ID': 100001, 'Loan_Type': 'AUTO', 'Loan_Amount': 28500.00, 'Interest_Rate': 4.25, 'Term_Months': 60, 'Monthly_Payment': 532.45, 'Balance_Remaining': 15230.67, 'Origination_Date': datetime(2022, 6, 15), 'Status': 'CURRENT', 'Credit_Score': 745},
            {'Loan_ID': 30002, 'Member_ID': 100002, 'Loan_Type': 'PERSONAL', 'Loan_Amount': 15000.00, 'Interest_Rate': 8.75, 'Term_Months': 48, 'Monthly_Payment': 367.89, 'Balance_Remaining': 8456.23, 'Origination_Date': datetime(2023, 2, 10), 'Status': 'CURRENT', 'Credit_Score': 689},
            {'Loan_ID': 30003, 'Member_ID': 100003, 'Loan_Type': 'MORTGAGE', 'Loan_Amount': 325000.00, 'Interest_Rate': 6.875, 'Term_Months': 360, 'Monthly_Payment': 2140.67, 'Balance_Remaining': 318500.45, 'Origination_Date': datetime(2023, 8, 1), 'Status': 'CURRENT', 'Credit_Score': 712},
            {'Loan_ID': 30004, 'Member_ID': 100004, 'Loan_Type': 'AUTO', 'Loan_Amount': 22000.00, 'Interest_Rate': 5.50, 'Term_Months': 72, 'Monthly_Payment': 348.90, 'Balance_Remaining': 19876.34, 'Origination_Date': datetime(2023, 10, 20), 'Status': 'DELINQUENT', 'Credit_Score': 658},
            {'Loan_ID': 30005, 'Member_ID': 100006, 'Loan_Type': 'HOME_EQUITY', 'Loan_Amount': 75000.00, 'Interest_Rate': 7.25, 'Term_Months': 120, 'Monthly_Payment': 890.23, 'Balance_Remaining': 67234.78, 'Origination_Date': datetime(2022, 3, 12), 'Status': 'CURRENT', 'Credit_Score': 798},
            {'Loan_ID': 30006, 'Member_ID': 100007, 'Loan_Type': 'PERSONAL', 'Loan_Amount': 8500.00, 'Interest_Rate': 9.25, 'Term_Months': 36, 'Monthly_Payment': 271.45, 'Balance_Remaining': 6789.12, 'Origination_Date': datetime(2023, 6, 5), 'Status': 'CURRENT', 'Credit_Score': 701},
            {'Loan_ID': 30007, 'Member_ID': 100008, 'Loan_Type': 'AUTO', 'Loan_Amount': 31500.00, 'Interest_Rate': 4.75, 'Term_Months': 60, 'Monthly_Payment': 590.34, 'Balance_Remaining': 12450.89, 'Origination_Date': datetime(2022, 1, 18), 'Status': 'CURRENT', 'Credit_Score': 675}
        ]
        
        self.sample_transactions = [
            {'Transaction_ID': 40001, 'Account_ID': 20001, 'Member_ID': 100001, 'Transaction_Type': 'DEBIT', 'Amount': -45.67, 'Description': 'GROCERY STORE', 'Transaction_Date': datetime.now() - timedelta(days=1), 'Balance_After': 3245.67},
            {'Transaction_ID': 40002, 'Account_ID': 20002, 'Member_ID': 100001, 'Transaction_Type': 'DEPOSIT', 'Amount': 2500.00, 'Description': 'PAYROLL DEPOSIT', 'Transaction_Date': datetime.now() - timedelta(days=2), 'Balance_After': 15780.23},
            {'Transaction_ID': 40003, 'Account_ID': 20003, 'Member_ID': 100002, 'Transaction_Type': 'ATM_WITHDRAWAL', 'Amount': -100.00, 'Description': 'ATM WITHDRAWAL', 'Transaction_Date': datetime.now() - timedelta(days=1), 'Balance_After': 1892.45},
            {'Transaction_ID': 40004, 'Account_ID': 20005, 'Member_ID': 100003, 'Transaction_Type': 'CHECK', 'Amount': -1250.00, 'Description': 'RENT PAYMENT', 'Transaction_Date': datetime.now() - timedelta(days=3), 'Balance_After': 2156.78},
            {'Transaction_ID': 40005, 'Account_ID': 20007, 'Member_ID': 100004, 'Transaction_Type': 'CASH', 'Amount': 12500.00, 'Description': 'LARGE CASH DEPOSIT', 'Transaction_Date': datetime.now() - timedelta(days=5), 'Balance_After': 567.23},
            {'Transaction_ID': 40006, 'Account_ID': 20008, 'Member_ID': 100005, 'Transaction_Type': 'TRANSFER', 'Amount': 500.00, 'Description': 'TRANSFER FROM SAVINGS', 'Transaction_Date': datetime.now() - timedelta(hours=12), 'Balance_After': 4123.89}
        ]
        
        self.sample_branches = [
            {'Branch_ID': 1, 'Branch_Name': 'Downtown Portland', 'Address': '100 SW Main St', 'City': 'Portland', 'State': 'OR', 'ZIP': '97204', 'Phone': '503-555-0100', 'Manager': 'Janet Smith'},
            {'Branch_ID': 2, 'Branch_Name': 'Beaverton Branch', 'Address': '5555 SW Hall Blvd', 'City': 'Beaverton', 'State': 'OR', 'ZIP': '97005', 'Phone': '503-555-0200', 'Manager': 'Mark Johnson'},
            {'Branch_ID': 3, 'Branch_Name': 'Gresham Branch', 'Address': '1234 NE Burnside Rd', 'City': 'Gresham', 'State': 'OR', 'ZIP': '97030', 'Phone': '503-555-0300', 'Manager': 'Lisa Rodriguez'}
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
        
    def _convert_datetime_for_json(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert datetime objects to ISO format strings for JSON serialization."""
        converted_data = []
        for row in data:
            converted_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    converted_row[key] = value.isoformat()
                else:
                    converted_row[key] = value
            converted_data.append(converted_row)
        return converted_data

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
            result = None
            if "ai_agents" in sql_lower:
                result = self._filter_mock_data(self.mock_tables['AI_Agents'], sql)
            elif "ai_messages" in sql_lower:
                result = self._filter_mock_data(self.mock_tables['AI_Messages'], sql)
            elif "ai_memories" in sql_lower:
                result = self._filter_mock_data(self.mock_tables['AI_Memories'], sql)
            elif "ai_query_history" in sql_lower:
                result = self._filter_mock_data(self.mock_tables['AI_Query_History'], sql)
            elif "members" in sql_lower:
                result = self._filter_mock_data(self.sample_members, sql)
            elif "accounts" in sql_lower:
                result = self._filter_mock_data(self.sample_accounts, sql)
            elif "loans" in sql_lower:
                result = self._filter_mock_data(self.sample_loans, sql)
            elif "transactions" in sql_lower:
                result = self._filter_mock_data(self.sample_transactions, sql)
            elif "branches" in sql_lower:
                result = self._filter_mock_data(self.sample_branches, sql)
            elif "select 1" in sql_lower:
                result = [{'result': 1}]
            elif "count(*)" in sql_lower:
                result = [{'cnt': random.randint(0, 100)}]
            else:
                # Generic response for unknown queries
                result = [
                    {'column1': 'Sample Value 1', 'column2': 123, 'column3': datetime.now()},
                    {'column1': 'Sample Value 2', 'column2': 456, 'column3': datetime.now() - timedelta(days=1)}
                ]
            
            # Convert datetime objects to JSON-serializable strings
            return self._convert_datetime_for_json(result)
                
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
            filtered_data = data[:]  # Start with all data
            
            # Handle conversation history queries with OR conditions
            if "user_from =" in sql_lower and "user_to =" in sql_lower and " or " in sql_lower:
                # This is likely a conversation history query
                # Pattern: WHERE (user_from = 'A' AND user_to = 'B') OR (user_from = 'B' AND user_to = 'A')
                import re
                
                # Extract the user values
                users = re.findall(r"user_(?:from|to) = '([^']+)'", sql_lower)
                self.log(f"Mock: Conversation query found {len(users)} users: {users}")
                self.log(f"Mock: Total messages in database: {len(filtered_data)}")
                
                if len(users) >= 2:
                    user1, user2 = users[0], users[1]
                    self.log(f"Mock: Filtering for messages between {user1} and {user2}")
                    
                    # Debug: show first few messages
                    for i, msg in enumerate(filtered_data[:5]):
                        self.log(f"Mock: Message {i}: From={msg.get('User_From')} To={msg.get('User_To')} Text={msg.get('Message', '')[:30]}...")
                    
                    # Filter for messages between these two users (case insensitive)
                    original_count = len(filtered_data)
                    filtered_data = [
                        row for row in filtered_data 
                        if (row.get('User_From', '').lower() == user1.lower() and row.get('User_To', '').lower() == user2.lower()) or
                           (row.get('User_From', '').lower() == user2.lower() and row.get('User_To', '').lower() == user1.lower())
                    ]
                    self.log(f"Mock: Filtered from {original_count} to {len(filtered_data)} messages")
                
            # Look for common patterns
            elif "state = 'ca'" in sql_lower or 'state = "ca"' in sql_lower:
                filtered_data = [row for row in filtered_data if row.get('State') == 'CA']
                
            elif "agent =" in sql_lower:
                # Extract agent name (very basic parsing)
                parts = sql_lower.split("agent =")
                if len(parts) > 1:
                    agent_part = parts[1].strip()
                    agent_name = agent_part.split()[0].strip("'\"")
                    filtered_data = [row for row in filtered_data if row.get('Agent', '').lower() == agent_name.lower()]
                    
            # Handle user_to filtering for messages
            elif "user_to =" in sql_lower:
                # Extract user_to value
                user_to_start = sql_lower.find("user_to =") + len("user_to =")
                user_to_part = sql_lower[user_to_start:].strip()
                if user_to_part.startswith("'") or user_to_part.startswith('"'):
                    quote_char = user_to_part[0]
                    end_quote = user_to_part.find(quote_char, 1)
                    if end_quote > 0:
                        user_to_value = user_to_part[1:end_quote]
                        filtered_data = [row for row in filtered_data if row.get('User_To') == user_to_value]
                        
            # Handle user_read IS NULL filtering
            if "user_read is null" in sql_lower:
                filtered_data = [row for row in filtered_data if row.get('User_Read') is None]
                
        else:
            filtered_data = data[:]
            
        # Apply ORDER BY if present
        if "order by" in sql_lower:
            try:
                order_part = sql_lower.split("order by")[1].strip()
                # Handle simple cases like "ORDER BY posted DESC"
                if "posted desc" in order_part:
                    # Sort by Posted field in descending order
                    filtered_data.sort(key=lambda x: x.get('Posted', datetime.min), reverse=True)
                elif "posted asc" in order_part or "posted" in order_part:
                    # Sort by Posted field in ascending order
                    filtered_data.sort(key=lambda x: x.get('Posted', datetime.min), reverse=False)
            except:
                pass  # Ignore ordering errors
                    
        # Apply LIMIT if present
        if "limit" in sql_lower:
            try:
                limit_part = sql_lower.split("limit")[1].strip()
                limit_num = int(limit_part.split()[0])
                filtered_data = filtered_data[:limit_num]
            except (IndexError, ValueError):
                pass
                
        return filtered_data
        
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
            # Parse INSERT statement to extract actual values
            import re
            
            # Extract values from INSERT statement
            # Pattern: INSERT INTO AI_Messages (columns) VALUES (values)
            values_match = re.search(r"values\s*\([^)]+\)", sql_lower)
            if values_match:
                values_str = values_match.group(0)
                # Extract individual values (handle quotes)
                value_matches = re.findall(r"'([^']*)'", values_str)
                
                if len(value_matches) >= 3:  # user_from, user_to, message
                    new_message = {
                        'Message_ID': len(self.mock_tables['AI_Messages']) + 1,
                        'Posted': datetime.now(),
                        'User_From': value_matches[0],
                        'User_To': value_matches[1], 
                        'Message': value_matches[2],
                        'User_Read': None
                    }
                    self.mock_tables['AI_Messages'].append(new_message)
                    self.log(f"Mock: Added message from {value_matches[0]} to {value_matches[1]}: {value_matches[2][:50]}...")
                else:
                    # Fallback to mock data
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
            # Add all messages to mock table (not just first 5)
            for item in data:
                # Ensure proper field name casing for consistency with existing data
                new_message = {
                    'Message_ID': len(self.mock_tables['AI_Messages']) + 1,
                    'Posted': item.get('posted', datetime.now()),
                    'User_From': item.get('user_from', 'unknown'),
                    'User_To': item.get('user_to', 'unknown'),
                    'Message': item.get('message', ''),
                    'User_Read': item.get('user_read', None)
                }
                self.mock_tables['AI_Messages'].append(new_message)
                self.log(f"Mock: Added message from {new_message['User_From']} to {new_message['User_To']}: {new_message['Message'][:50]}...")
            
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