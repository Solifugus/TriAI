"""
Test script for MockDataLink only (no dependencies required).
"""

import sys
from datetime import datetime
from mock_datalink import MockDataLink


def test_mock_datalink():
    """Test the MockDataLink implementation."""
    print("=" * 50)
    print("Testing MockDataLink")
    print("=" * 50)
    
    # Initialize mock DataLink
    mock_instances = [{"instance": "mock\\server", "user": "mock_user", "password": "mock_pass"}]
    db = MockDataLink(mock_instances, home_db="MockDB", debug=True)
    
    try:
        # Test basic query
        print("\n1. Testing basic query (AI_Agents):")
        agents = db.sql_get("SELECT * FROM AI_Agents")
        print(f"Found {len(agents)} agents:")
        for agent in agents:
            print(f"  - {agent['Agent']}: {agent['Description']}")
            
        # Test filtered query
        print("\n2. Testing filtered query (Messages for DataAnalyst):")
        messages = db.sql_get("SELECT * FROM AI_Messages WHERE User_To = 'DataAnalyst'")
        print(f"Found {len(messages)} messages for DataAnalyst")
        
        # Test data conversion
        print("\n3. Testing data conversion:")
        agents_cols = db.to_columns(agents)
        print(f"Converted to columns: {list(agents_cols.keys())}")
        agents_rows = db.to_rows(agents_cols)
        print(f"Converted back to rows: {len(agents_rows)} rows")
        
        # Test insert operation
        print("\n4. Testing insert operation:")
        new_message = [{
            'User_From': 'testuser',
            'User_To': 'DataAnalyst', 
            'Message': 'Test message from test script',
            'Posted': datetime.now()
        }]
        db.sql_insert('AI_Messages', new_message)
        print("Insert operation completed")
        
        # Test SQL generation without execution
        print("\n5. Testing SQL generation:")
        sql = db.sql_insert('AI_Messages', new_message, run=False)
        print(f"Generated SQL: {sql}")
        
        # Test error handling
        print("\n6. Testing error handling:")
        try:
            db.sql_get("INVALID SQL QUERY")
        except Exception as e:
            print(f"Caught expected error: {str(e)[:100]}...")
            print(f"Error flag set: {db.wasError}")
            
        # Test logging
        print("\n7. Testing logging:")
        db.log("Test log message")
        recent_logs = db.read_log(3)
        print(f"Recent log entries ({len(recent_logs)}):")
        for log_entry in recent_logs:
            print(f"  {log_entry}")
            
        print("\n✅ MockDataLink tests completed successfully!")
        
    except Exception as e:
        print(f"❌ MockDataLink test failed: {str(e)}")
        return False
        
    return True


def test_sql_escape():
    """Test SQL escaping functionality."""
    print("\n" + "=" * 30)
    print("Testing SQL Escaping")
    print("=" * 30)
    
    db = MockDataLink([], debug=False)
    
    test_cases = [
        ("O'Brien", "'O''Brien'"),
        ("Test's string", "'Test''s string'"),  
        ("Normal string", "'Normal string'"),
        (None, "NULL"),
        (123, "'123'"),
        ("Don't do 'this'", "'Don''t do ''this'''")
    ]
    
    all_passed = True
    for input_val, expected in test_cases:
        result = db.sql_escape(input_val)
        if result == expected:
            print(f"✅ {input_val} -> {result}")
        else:
            print(f"❌ {input_val} -> {result} (expected {expected})")
            all_passed = False
            
    return all_passed


def main():
    """Run MockDataLink tests only."""
    print("MockDataLink Implementation Tests")
    print("=================================")
    
    tests_passed = 0
    total_tests = 2
    
    # Test MockDataLink
    if test_mock_datalink():
        tests_passed += 1
        
    # Test SQL escaping  
    if test_sql_escape():
        tests_passed += 1
        
    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    print("=" * 50)
    
    if tests_passed == total_tests:
        print("🎉 All tests completed successfully!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())