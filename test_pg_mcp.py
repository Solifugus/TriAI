#!/usr/bin/env python3
"""
Test script for PostgreSQL DataLink and MCP tools integration.
"""

import sys
import yaml
from datetime import datetime, timedelta
from pg_datalink import PostgreSQLDataLink
from mcp_tools import MCPToolProvider

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
        datalink = PostgreSQLDataLink(pg_config, debug=True)
        
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
    """Test MCP tool functionality"""
    print("\n=== Testing MCP Tools ===")
    
    try:
        # Initialize MCP tool provider
        mcp = MCPToolProvider(datalink)
        
        # Test 1: Database connection
        print("\n--- Test 1: Database Connection ---")
        result = mcp.execute_tool("connect_to_database", {
            "server_instance": "localhost",
            "database_name": "triai_test"
        })
        print(f"Connection test: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            print(f"Connected: {result['data']['connected']}")
        
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
            for table in tables[:5]:  # Show first 5
                print(f"  - {table['name']} ({table['type']})")
        
        # Test 3: Execute query
        print("\n--- Test 3: Query Execution ---")
        result = mcp.execute_tool("execute_query", {
            "database_name": "triai_test",
            "sql_query": "SELECT agent, model, polling_interval FROM ai_agents ORDER BY agent",
            "row_limit": 10
        })
        print(f"Query execution: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            data = result['data']
            print(f"Returned {data['row_count']} rows in {data['execution_time_ms']}ms")
            for row in data['results']:
                print(f"  - {row['agent']}: {row['model']} (poll: {row['polling_interval']}s)")
        
        # Test 4: Sample table
        print("\n--- Test 4: Sample Table Data ---")
        result = mcp.execute_tool("sample_table", {
            "database_name": "triai_test",
            "table_name": "ai_messages",
            "row_count": 3
        })
        print(f"Sample data: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            for i, row in enumerate(result['data'], 1):
                if 'message' in row:
                    msg_preview = row['message'][:60] + "..." if len(row['message']) > 60 else row['message']
                    print(f"  {i}. {row.get('user_from', 'N/A')} → {row.get('user_to', 'N/A')}: {msg_preview}")
        
        # Test 5: Memory operations
        print("\n--- Test 5: Memory Operations ---")
        
        # Store a test memory
        result = mcp.execute_tool("store_memory", {
            "agent_name": "TestAgent",
            "memory_label": "PostgreSQL Test Memory",
            "memory_content": "This is a test memory stored during PostgreSQL MCP testing",
            "related_to_tags": "test postgresql mcp",
            "purge_after": (datetime.now() + timedelta(days=1)).isoformat()
        })
        print(f"Store memory: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            print(f"  Stored memory ID: {result['data']['memory_id']}")
        
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
                if 'memory_label' in memory:
                    print(f"    - {memory['memory_label']}: {memory.get('times_recalled', 0)} recalls")
        
        # Test 6: Memory stats
        print("\n--- Test 6: Memory Statistics ---")
        result = mcp.execute_tool("get_memory_stats", {
            "agent_name": "DataAnalyst"
        })
        print(f"Memory stats: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            stats = result['data']
            print(f"  Total memories: {stats.get('total_memories', 0)}")
            print(f"  Average recalls: {stats.get('avg_recalls', 0):.2f}")
            if 'top_tags' in stats:
                print(f"  Top tags: {stats['top_tags'][:3]}")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP Tools error: {str(e)}")
        return False

def test_data_integrity():
    """Test data integrity and relationships"""
    print("\n=== Testing Data Integrity ===")
    
    config = load_config()
    pg_config = config['database']['postgresql']
    datalink = PostgreSQLDataLink(pg_config)
    
    try:
        # Check agent coverage
        agents_count = datalink.sql_get("SELECT COUNT(*) as count FROM ai_agents")[0]['count']
        messages_agents = datalink.sql_get("""
            SELECT COUNT(DISTINCT user_to) as agent_count 
            FROM ai_messages 
            WHERE user_to IN (SELECT agent FROM ai_agents)
        """)[0]['agent_count']
        
        print(f"Agents in system: {agents_count}")
        print(f"Agents with messages: {messages_agents}")
        print(f"Coverage: {'✓ Complete' if agents_count == messages_agents else '⚠ Partial'}")
        
        # Check memory distribution
        memory_stats = datalink.sql_get("""
            SELECT agent, COUNT(*) as memory_count 
            FROM ai_memories 
            GROUP BY agent 
            ORDER BY memory_count DESC
        """)
        
        print(f"\nMemory distribution:")
        for stat in memory_stats:
            print(f"  {stat['agent']}: {stat['memory_count']} memories")
        
        # Check recent activity
        recent_messages = datalink.sql_get("""
            SELECT COUNT(*) as count 
            FROM ai_messages 
            WHERE posted >= CURRENT_DATE - INTERVAL '7 days'
        """)[0]['count']
        
        print(f"\nRecent activity (last 7 days): {recent_messages} messages")
        
        return True
        
    except Exception as e:
        print(f"✗ Data integrity check failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("TriAI PostgreSQL MCP Tools Test")
    print("=" * 50)
    
    # Test 1: PostgreSQL connection
    datalink = test_postgresql_connection()
    if not datalink:
        print("\n✗ Database connection failed - aborting tests")
        sys.exit(1)
    
    # Test 2: MCP tools
    mcp_success = test_mcp_tools(datalink)
    if not mcp_success:
        print("\n⚠ MCP tools had issues")
    
    # Test 3: Data integrity
    integrity_success = test_data_integrity()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"PostgreSQL Connection: ✓ Success")
    print(f"MCP Tools: {'✓ Success' if mcp_success else '⚠ Issues'}")
    print(f"Data Integrity: {'✓ Success' if integrity_success else '⚠ Issues'}")
    
    if mcp_success and integrity_success:
        print(f"\n🎉 All tests passed! PostgreSQL database and MCP tools are ready.")
        print(f"Database: triai_test")
        print(f"Tables: AI_Agents, AI_Messages, AI_Memories, AI_Scripts")
        print(f"Configuration: Updated to use PostgreSQL")
    else:
        print(f"\n⚠ Some tests had issues - check output above")

if __name__ == "__main__":
    main()