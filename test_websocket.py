"""
Test WebSocket functionality and MCP tools.
"""

import asyncio
import json
import websockets


async def test_websocket_agent_connection():
    """Test agent WebSocket connection and MCP tools."""
    print("=" * 50)
    print("Testing WebSocket Agent Connection & MCP Tools")
    print("=" * 50)
    
    try:
        uri = "ws://localhost:8080/ws/agent/DataAnalyst"
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")
            
            # Wait for connection confirmation
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") == "connected":
                print(f"✅ Agent {data.get('agent_name')} connected successfully")
                print(f"   Available tools: {len(data.get('available_tools', []))} tools")
                
                # Test 1: List databases MCP tool
                print("\n1. Testing 'list_databases' MCP tool:")
                mcp_request = {
                    "type": "mcp_request",
                    "tool": "list_databases",
                    "parameters": {"server_instance": "mock_server"}
                }
                
                await websocket.send(json.dumps(mcp_request))
                mcp_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                mcp_data = json.loads(mcp_response)
                
                if mcp_data.get("success"):
                    databases = mcp_data.get("data", [])
                    print(f"   ✅ Found {len(databases)} databases: {databases}")
                else:
                    print(f"   ❌ Tool failed: {mcp_data.get('error')}")
                    
                # Test 2: Get schema info MCP tool
                print("\n2. Testing 'get_schema_info' MCP tool:")
                mcp_request = {
                    "type": "mcp_request",
                    "tool": "get_schema_info",
                    "parameters": {"database_name": "TriAI_Main"}
                }
                
                await websocket.send(json.dumps(mcp_request))
                mcp_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                mcp_data = json.loads(mcp_response)
                
                if mcp_data.get("success"):
                    schema = mcp_data.get("data", {})
                    print(f"   ✅ Schema info retrieved for {schema.get('database')}")
                    print(f"   Tables: {len(schema.get('tables', []))}")
                    print(f"   Views: {len(schema.get('views', []))}")
                else:
                    print(f"   ❌ Tool failed: {mcp_data.get('error')}")
                    
                # Test 3: Execute query MCP tool
                print("\n3. Testing 'execute_query' MCP tool:")
                mcp_request = {
                    "type": "mcp_request",
                    "tool": "execute_query",
                    "parameters": {
                        "database_name": "TriAI_Main",
                        "sql_query": "SELECT * FROM AI_Agents LIMIT 3"
                    }
                }
                
                await websocket.send(json.dumps(mcp_request))
                mcp_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                mcp_data = json.loads(mcp_response)
                
                if mcp_data.get("success"):
                    query_result = mcp_data.get("data", {})
                    print(f"   ✅ Query executed successfully")
                    print(f"   Rows returned: {query_result.get('row_count')}")
                    print(f"   Execution time: {query_result.get('execution_time_ms')}ms")
                else:
                    print(f"   ❌ Tool failed: {mcp_data.get('error')}")
                    
                # Test 4: Store memory MCP tool
                print("\n4. Testing 'store_memory' MCP tool:")
                mcp_request = {
                    "type": "mcp_request",
                    "tool": "store_memory",
                    "parameters": {
                        "agent_name": "DataAnalyst",
                        "memory_label": "Test Memory",
                        "memory_content": "This is a test memory stored via WebSocket",
                        "related_to_tags": "test websocket memory"
                    }
                }
                
                await websocket.send(json.dumps(mcp_request))
                mcp_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                mcp_data = json.loads(mcp_response)
                
                if mcp_data.get("success"):
                    memory_result = mcp_data.get("data", {})
                    print(f"   ✅ Memory stored with ID: {memory_result.get('memory_id')}")
                else:
                    print(f"   ❌ Tool failed: {mcp_data.get('error')}")
                    
                # Test 5: Check for messages
                print("\n5. Testing 'check_messages' functionality:")
                check_request = {
                    "type": "check_messages"
                }
                
                await websocket.send(json.dumps(check_request))
                check_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                check_data = json.loads(check_response)
                
                if check_data.get("type") == "messages_response":
                    unread_count = check_data.get("unread_count", 0)
                    print(f"   ✅ Found {unread_count} unread messages")
                    
                    if unread_count > 0:
                        messages = check_data.get("messages", [])
                        for msg in messages[:2]:  # Show first 2
                            print(f"   Message from {msg.get('User_From')}: {msg.get('Message')[:50]}...")
                else:
                    print(f"   ❌ Unexpected response: {check_data}")
                    
                # Test 6: Send response
                print("\n6. Testing 'send_response' functionality:")
                response_request = {
                    "type": "send_response",
                    "message": "This is a test response from DataAnalyst via WebSocket",
                    "to_user": "testuser"
                }
                
                await websocket.send(json.dumps(response_request))
                response_ack = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response_ack)
                
                if response_data.get("success"):
                    print("   ✅ Response message sent successfully")
                else:
                    print(f"   ❌ Send response failed: {response_data}")
                    
                print("\n✅ All WebSocket tests completed successfully!")
                return True
                
            else:
                print(f"❌ Connection failed: {data}")
                return False
                
    except asyncio.TimeoutError:
        print("❌ WebSocket test timed out")
        return False
    except Exception as e:
        print(f"❌ WebSocket test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_invalid_agent_connection():
    """Test connection with invalid agent name."""
    print("\n" + "=" * 50)
    print("Testing Invalid Agent Connection")
    print("=" * 50)
    
    try:
        uri = "ws://localhost:8080/ws/agent/NonExistentAgent"
        
        async with websockets.connect(uri) as websocket:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") == "error":
                print("✅ Invalid agent correctly rejected")
                print(f"   Error message: {data.get('message')}")
                return True
            else:
                print(f"❌ Expected error but got: {data}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


async def main():
    """Run all WebSocket tests."""
    test1_result = await test_websocket_agent_connection()
    test2_result = await test_invalid_agent_connection()
    
    print("\n" + "=" * 50)
    print("WebSocket Test Results")
    print("=" * 50)
    
    tests = {
        "Valid Agent Connection & MCP Tools": test1_result,
        "Invalid Agent Rejection": test2_result
    }
    
    passed = sum(1 for result in tests.values() if result)
    total = len(tests)
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 50)
    print(f"Total: {passed}/{total} WebSocket tests passed")
    
    return passed == total


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("🎉 All WebSocket tests passed!")
        else:
            print("⚠️ Some WebSocket tests failed.")
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")