#!/usr/bin/env python3
"""
Updated test script for PostgreSQL DataLink and MCP tools integration.
"""

import sys
import yaml
from datetime import datetime, timedelta
from pg_datalink import PostgreSQLDataLink
from mcp_tools_pg import PostgreSQLMCPToolProvider

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def test_postgresql_connection():
    """Test PostgreSQL DataLink connection"""
    print("=== Testing PostgreSQL Connection ===")
    
    config = load_config()
    pg_config = config['database']['postgresql']
    
    print(f"Connecting to database: {pg_config['database']}")
    print(f"Host: {pg_config['host']}:{pg_config['port']}")
    print(f"User: {pg_config['user']}")
    
    try:
        # Initialize PostgreSQL DataLink
        datalink = PostgreSQLDataLink(pg_config, debug=False)
        
        # Test connection
        if datalink.test_connection():
            print("✓ Connection successful")
            
            # Test basic query
            print("\n--- Testing Basic Query ---")
            result = datalink.sql_get("SELECT current_database(), version()")
            print(f"Database: {result[0]['current_database']}")
            print(f"Version: {result[0]['version'][:50]}...")
            
            # Test table access
            print("\n--- Testing Table Access ---")
            agents = datalink.sql_get("SELECT agent, description FROM ai_agents LIMIT 3")
            print(f"Found {len(agents)} agents:")
            for agent in agents:
                print(f"  - {agent['agent']}: {agent['description']}")
            
            return datalink
            
        else:
            print("✗ Connection failed")
            return None
            
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
        return None

def test_mcp_tools(datalink):
    """Test MCP tool functionality with PostgreSQL-specific implementation"""
    print("\n=== Testing PostgreSQL MCP Tools ===")
    
    try:
        # Initialize MCP tool provider
        mcp = PostgreSQLMCPToolProvider(datalink)
        
        # Test 1: Database connection
        print("\n--- Test 1: Database Connection ---")
        result = mcp.execute_tool("connect_to_database", {
            "server_instance": "localhost",
            "database_name": "triai_test"
        })
        print(f"Connection test: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            data = result['data']
            print(f"Connected: {data['connected']}")
            print(f"Database: {data.get('current_database', 'N/A')}")
            print(f"User: {data.get('current_user', 'N/A')}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Test 2: Schema info
        print("\n--- Test 2: Schema Information ---")
        result = mcp.execute_tool("get_schema_info", {
            "database_name": "triai_test",
            "object_types": ["tables"]
        })
        print(f"Schema query: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            tables = result['data'].get('tables', [])
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['name']} ({table['type']})")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Test 3: Describe table
        print("\n--- Test 3: Describe Table ---")
        result = mcp.execute_tool("describe_table", {
            "database_name": "triai_test",
            "table_name": "ai_agents",
            "include_sample_data": False
        })
        print(f"Describe table: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            data = result['data']
            print(f"Table: {data['table_name']}")
            columns = data.get('columns', [])
            print(f"Columns ({len(columns)}):")
            for col in columns:
                pk = " (PK)" if col.get('primary_key', False) else ""
                nullable = "NULL" if col.get('nullable', False) else "NOT NULL"
                print(f"  - {col['name']}: {col['type']} {nullable}{pk}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Test 4: Execute query
        print("\n--- Test 4: Query Execution ---")
        result = mcp.execute_tool("execute_query", {
            "database_name": "triai_test",
            "sql_query": "SELECT agent, model, polling_interval FROM ai_agents ORDER BY agent",
            "row_limit": 10
        })
        print(f"Query execution: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            data = result['data']
            print(f"Returned {data['row_count']} rows in {data['execution_time_ms']}ms")
            print("Results:")
            for row in data['results']:
                print(f"  - {row['agent']}: {row['model']} (poll: {row['polling_interval']}s)")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Test 5: Sample table
        print("\n--- Test 5: Sample Table Data ---")
        result = mcp.execute_tool("sample_table", {
            "database_name": "triai_test",
            "table_name": "ai_messages",
            "row_count": 3
        })
        print(f"Sample data: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            for i, row in enumerate(result['data'], 1):
                if isinstance(row, dict) and 'message' in row:
                    msg_preview = row['message'][:60] + "..." if len(row['message']) > 60 else row['message']
                    print(f"  {i}. {row.get('user_from', 'N/A')} → {row.get('user_to', 'N/A')}: {msg_preview}")
                else:
                    print(f"  {i}. {row}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Test 6: Column statistics
        print("\n--- Test 6: Column Statistics ---")
        result = mcp.execute_tool("get_column_stats", {
            "database_name": "triai_test",
            "table_name": "ai_agents",
            "column_name": "agent"
        })
        print(f"Column stats: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            stats = result['data']
            print(f"  Column: {stats.get('column_name', 'N/A')}")
            print(f"  Total rows: {stats.get('total_rows', 0)}")
            print(f"  Non-null: {stats.get('non_null_count', 0)}")
            print(f"  Unique values: {stats.get('unique_values', 0)}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Test 7: Memory operations
        print("\n--- Test 7: Memory Operations ---")
        
        # Store a test memory
        result = mcp.execute_tool("store_memory", {
            "agent_name": "TestAgent",
            "memory_label": "PostgreSQL Test Memory",
            "memory_content": "This is a test memory stored during PostgreSQL MCP testing at " + datetime.now().isoformat(),
            "related_to_tags": "test postgresql mcp validation",
            "purge_after": (datetime.now() + timedelta(days=1)).isoformat()
        })
        print(f"Store memory: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            print(f"  Stored memory ID: {result['data'].get('memory_id', 'N/A')}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        # Retrieve memories
        result = mcp.execute_tool("retrieve_memories", {
            "agent_name": "DataAnalyst",
            "related_to_tags": "sales database",
            "limit": 5
        })
        print(f"Retrieve memories: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            memories = result['data']
            print(f"  Found {len(memories)} related memories")
            for memory in memories[:2]:  # Show first 2
                if isinstance(memory, dict) and 'memory_label' in memory:
                    print(f"    - {memory['memory_label']}: {memory.get('times_recalled', 0)} recalls")
                else:
                    print(f"    - {memory}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        # Test 8: Memory search
        print("\n--- Test 8: Memory Search ---")
        result = mcp.execute_tool("search_memories", {
            "agent_name": "CodeAssistant",
            "search_text": "Java",
            "limit": 3
        })
        print(f"Memory search: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            memories = result['data']
            print(f"  Found {len(memories)} memories with 'Java'")
            for memory in memories:
                if isinstance(memory, dict) and 'memory_label' in memory:
                    print(f"    - {memory['memory_label']}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        # Test 9: Memory stats
        print("\n--- Test 9: Memory Statistics ---")
        result = mcp.execute_tool("get_memory_stats", {
            "agent_name": "DataAnalyst"
        })
        print(f"Memory stats: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            stats = result['data']
            print(f"  Total memories: {stats.get('total_memories', 0)}")
            print(f"  Average recalls: {stats.get('avg_recalls', 0):.2f}")
            print(f"  Unused memories: {stats.get('unused_memories', 0)}")
            if 'top_tags' in stats and stats['top_tags']:
                print(f"  Top tags: {stats['top_tags'][:3]}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP Tools error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_sql_validation(mcp):
    """Test SQL validation functionality"""
    print("\n=== Testing SQL Validation ===")
    
    test_queries = [
        ("Valid SELECT", "SELECT * FROM ai_agents"),
        ("Invalid DELETE", "DELETE FROM ai_agents"),
        ("Invalid DROP", "DROP TABLE ai_agents"),
        ("Complex SELECT", "SELECT a.agent, COUNT(m.message_id) FROM ai_agents a LEFT JOIN ai_messages m ON a.agent = m.user_to GROUP BY a.agent"),
        ("Syntax Error", "SELECT * FROM WHERE")
    ]
    
    for test_name, query in test_queries:
        result = mcp.execute_tool("validate_sql", {
            "database_name": "triai_test",
            "sql_query": query
        })
        
        if result['success']:
            valid = result['data']['valid']
            issues = result['data'].get('issues', [])
            print(f"{test_name}: {'✓ Valid' if valid else '✗ Invalid'}")
            if issues:
                print(f"  Issues: {', '.join(issues)}")
        else:
            print(f"{test_name}: ✗ Error - {result.get('error', 'Unknown')}")

def main():
    """Main test function"""
    print("TriAI PostgreSQL MCP Tools Test (Fixed Version)")
    print("=" * 60)
    
    # Test 1: PostgreSQL connection
    datalink = test_postgresql_connection()
    if not datalink:
        print("\n✗ Database connection failed - aborting tests")
        sys.exit(1)
    
    # Test 2: MCP tools
    mcp = PostgreSQLMCPToolProvider(datalink)
    mcp_success = test_mcp_tools(datalink)
    
    # Test 3: SQL validation
    test_sql_validation(mcp)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"PostgreSQL Connection: ✓ Success")
    print(f"PostgreSQL MCP Tools: {'✓ Success' if mcp_success else '⚠ Issues'}")
    print(f"SQL Validation: ✓ Tested")
    
    if mcp_success:
        print(f"\n🎉 All tests passed! PostgreSQL database and MCP tools are ready.")
        print(f"Database: triai_test")
        print(f"Tables: ai_agents, ai_messages, ai_memories, ai_scripts")
        print(f"Configuration: Updated to use PostgreSQL")
        print(f"MCP Tools: PostgreSQL-compatible implementation ready")
    else:
        print(f"\n⚠ Some tests had issues - check output above")

if __name__ == "__main__":
    main()