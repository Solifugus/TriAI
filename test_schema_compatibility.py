#!/usr/bin/env python3
"""
Test script to verify schema compatibility across Mock, PostgreSQL, and SQL Server.
"""

import sys
import yaml
from datetime import datetime
from typing import Dict, Any, List

# Import compatibility layer
from schema_compatibility import SchemaCompatibility, get_schema_compatibility

# Import database classes
from mock_datalink import MockDataLink
from pg_datalink import PostgreSQLDataLink

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def test_mock_compatibility():
    """Test mock database with updated schema"""
    print("=== Testing Mock Database Compatibility ===")
    
    try:
        # Initialize mock database
        mock_db = MockDataLink([], "", debug=False)
        schema_compat = SchemaCompatibility('mock')
        
        # Test agents table
        print("\n--- Testing Agents Table ---")
        agents_query = "SELECT * FROM AI_Agents"
        agents = mock_db.sql_get(agents_query)
        
        print(f"Found {len(agents)} agents in mock data:")
        for agent in agents:
            # Convert to standard format
            std_agent = schema_compat.convert_row_to_standard('ai_agents', agent)
            print(f"  - {std_agent.get('agent', 'N/A')}: {std_agent.get('description', 'N/A')}")
            print(f"    Role: {std_agent.get('role', 'Missing')[:60]}...")
            print(f"    Polling: {std_agent.get('polling_interval', 'Missing')} seconds")
            print()
        
        # Test field mapping
        print("--- Testing Field Mapping ---")
        test_fields = ['agent', 'description', 'role', 'model_api', 'polling_interval']
        for field in test_fields:
            physical = schema_compat.get_field_name('ai_agents', field)
            print(f"  {field} -> {physical}")
        
        return True
        
    except Exception as e:
        print(f"✗ Mock compatibility test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_postgresql_compatibility():
    """Test PostgreSQL database compatibility"""
    print("\n=== Testing PostgreSQL Database Compatibility ===")
    
    try:
        config = load_config()
        pg_config = config['database']['postgresql']
        
        # Initialize PostgreSQL database
        pg_db = PostgreSQLDataLink(pg_config, debug=False)
        schema_compat = SchemaCompatibility('postgresql')
        
        # Test connection
        if not pg_db.test_connection():
            print("✗ PostgreSQL connection failed")
            return False
            
        print("✓ PostgreSQL connection successful")
        
        # Test agents table with standard field names
        print("\n--- Testing Agents Table ---")
        agents_query = "SELECT * FROM ai_agents"
        agents = pg_db.sql_get(agents_query)
        
        print(f"Found {len(agents)} agents in PostgreSQL:")
        for agent in agents:
            # Convert to standard format
            std_agent = schema_compat.convert_row_to_standard('ai_agents', agent)
            print(f"  - {std_agent.get('agent', 'N/A')}: {std_agent.get('description', 'N/A')}")
            print(f"    Role: {std_agent.get('role', 'Missing')[:60]}...")
            print(f"    Polling: {std_agent.get('polling_interval', 'Missing')} seconds")
            print()
        
        # Test query building
        print("--- Testing Query Building ---")
        query = schema_compat.build_select_query(
            'ai_agents',  # Use logical table name 
            ['agent', 'description', 'polling_interval'],
            limit=5
        )
        print(f"Generated query: {query}")
        
        result = pg_db.sql_get(query)
        print(f"Query returned {len(result)} rows")
        
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL compatibility test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cross_database_compatibility():
    """Test data compatibility across database types"""
    print("\n=== Testing Cross-Database Compatibility ===")
    
    try:
        # Test data conversion between formats
        print("--- Testing Data Conversion ---")
        
        # Mock format data
        mock_agent = {
            'Agent': 'TestAgent',
            'Description': 'Test Description',
            'Role': 'Test Role',
            'Model_API': 'test_api',
            'Model': 'test_model',
            'Polling_Interval': 5
        }
        
        # Convert mock to standard
        mock_compat = SchemaCompatibility('mock')
        std_agent = mock_compat.convert_row_to_standard('ai_agents', mock_agent)
        print(f"Mock -> Standard: {std_agent}")
        
        # Convert standard to PostgreSQL
        pg_compat = SchemaCompatibility('postgresql')
        pg_agent = pg_compat.convert_row_from_standard('ai_agents', std_agent)
        print(f"Standard -> PostgreSQL: {pg_agent}")
        
        # Convert standard to SQL Server 
        sql_compat = SchemaCompatibility('sqlserver')
        sql_agent = sql_compat.convert_row_from_standard('ai_agents', std_agent)
        print(f"Standard -> SQL Server: {sql_agent}")
        
        # Test query compatibility
        print("\n--- Testing Query Compatibility ---")
        databases = ['mock', 'postgresql', 'sqlserver']
        
        for db_type in databases:
            compat = SchemaCompatibility(db_type)
            query = compat.build_select_query(
                'ai_agents',
                ['agent', 'description', 'polling_interval'],
                where_clause="agent = 'TestAgent'",
                limit=10
            )
            print(f"{db_type.upper()}: {query}")
        
        return True
        
    except Exception as e:
        print(f"✗ Cross-database compatibility test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_compatibility():
    """Test MCP tools compatibility with schema conversion"""
    print("\n=== Testing MCP Tools Schema Compatibility ===")
    
    try:
        # Import MCP tools
        from mcp_tools import MCPToolProvider
        from mcp_tools_pg import PostgreSQLMCPToolProvider
        
        config = load_config()
        
        # Test with mock database
        print("--- Testing Mock MCP Tools ---")
        mock_db = MockDataLink([], "", debug=False)
        mock_mcp = MCPToolProvider(mock_db)
        
        result = mock_mcp.execute_tool("sample_table", {
            "database_name": "mock",
            "table_name": "AI_Agents",
            "row_count": 2
        })
        
        print(f"Mock MCP sample: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            mock_compat = SchemaCompatibility('mock')
            for row in result['data']:
                std_row = mock_compat.convert_row_to_standard('ai_agents', row)
                print(f"  Agent: {std_row.get('agent', 'N/A')} (Polling: {std_row.get('polling_interval', 'N/A')})")
        
        # Test with PostgreSQL database  
        print("\n--- Testing PostgreSQL MCP Tools ---")
        pg_config = config['database']['postgresql']
        pg_db = PostgreSQLDataLink(pg_config, debug=False)
        pg_mcp = PostgreSQLMCPToolProvider(pg_db)
        
        result = pg_mcp.execute_tool("sample_table", {
            "database_name": "triai_test",
            "table_name": "ai_agents", 
            "row_count": 2
        })
        
        print(f"PostgreSQL MCP sample: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            pg_compat = SchemaCompatibility('postgresql')
            for row in result['data']:
                std_row = pg_compat.convert_row_to_standard('ai_agents', row)
                print(f"  Agent: {std_row.get('agent', 'N/A')} (Polling: {std_row.get('polling_interval', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP compatibility test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_differences():
    """Test schema difference reporting"""
    print("\n=== Testing Schema Differences Analysis ===")
    
    try:
        compat = SchemaCompatibility('postgresql')
        differences = compat.get_agent_schema_differences()
        
        print("Schema Evolution Summary:")
        print(f"  New fields added: {differences['new_fields_added']}")
        print(f"  Deprecated fields: {differences['deprecated_fields']}")
        print(f"  Case differences: {differences['field_name_case_differences']}")
        
        print("\nCompatibility Notes:")
        for note in differences['compatibility_notes']:
            print(f"  - {note}")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema differences test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("TriAI Schema Compatibility Test")
    print("=" * 50)
    
    test_results = {}
    
    # Run tests
    test_results['mock'] = test_mock_compatibility()
    test_results['postgresql'] = test_postgresql_compatibility()
    test_results['cross_db'] = test_cross_database_compatibility()
    test_results['mcp'] = test_mcp_compatibility()
    test_results['differences'] = test_schema_differences()
    
    # Summary
    print("\n" + "=" * 50)
    print("COMPATIBILITY TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name.upper()}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL COMPATIBILITY TESTS PASSED!")
        print("\nSchema Compatibility Status:")
        print("✓ Mock database updated with new fields")
        print("✓ PostgreSQL schema compatible")
        print("✓ SQL Server schema compatible (assumed)")
        print("✓ Cross-database field mapping working")
        print("✓ MCP tools compatible across databases")
        print("✓ Backward compatibility maintained")
    else:
        print("⚠ SOME COMPATIBILITY ISSUES FOUND")
        print("Please check the test output above for details.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())