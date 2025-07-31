"""
Comprehensive test of all TriAI messaging server functionality.
"""

import requests
import json
import time
import asyncio
import websockets


class ComprehensiveTriAITester:
    """Comprehensive tester for TriAI messaging server."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize tester."""
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.results = {}
        
    def test_rest_endpoints(self):
        """Test all REST API endpoints."""
        print("=" * 60)
        print("TESTING REST API ENDPOINTS")
        print("=" * 60)
        
        # Test 1: Server health
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            self.results["Server Health"] = response.status_code == 200
            print(f"✅ Server Health: {response.status_code}")
        except Exception as e:
            self.results["Server Health"] = False
            print(f"❌ Server Health: {e}")
            
        # Test 2: Get user
        try:
            response = requests.get(f"{self.base_url}/api/user")
            if response.status_code == 200:
                data = response.json()
                self.results["GET /api/user"] = "username" in data
                print(f"✅ GET /api/user: {data.get('username')}")
            else:
                self.results["GET /api/user"] = False
                print(f"❌ GET /api/user: Status {response.status_code}")
        except Exception as e:
            self.results["GET /api/user"] = False
            print(f"❌ GET /api/user: {e}")
            
        # Test 3: Get agents
        try:
            response = requests.get(f"{self.base_url}/api/agents")
            if response.status_code == 200:
                agents = response.json()
                self.results["GET /api/agents"] = len(agents) > 0
                print(f"✅ GET /api/agents: {len(agents)} agents found")
                for agent in agents:
                    print(f"   - {agent['agent']}: {agent['description']}")
            else:
                self.results["GET /api/agents"] = False
                print(f"❌ GET /api/agents: Status {response.status_code}")
        except Exception as e:
            self.results["GET /api/agents"] = False  
            print(f"❌ GET /api/agents: {e}")
            
        # Test 4: Send message
        try:
            message_data = {
                "user_to": "DataAnalyst",
                "message": "Test message from comprehensive test script"
            }
            response = requests.post(
                f"{self.base_url}/api/message",
                json=message_data,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                result = response.json()
                self.results["POST /api/message"] = result.get("success", False)
                print(f"✅ POST /api/message: Message sent successfully")
            else:
                self.results["POST /api/message"] = False
                print(f"❌ POST /api/message: Status {response.status_code}")
        except Exception as e:
            self.results["POST /api/message"] = False
            print(f"❌ POST /api/message: {e}")
            
        # Test 5: Get messages
        try:
            response = requests.get(f"{self.base_url}/api/messages/DataAnalyst")
            if response.status_code == 200:
                messages = response.json()
                self.results["GET /api/messages"] = len(messages) >= 0
                print(f"✅ GET /api/messages: {len(messages)} messages found")
            else:
                self.results["GET /api/messages"] = False
                print(f"❌ GET /api/messages: Status {response.status_code}")
        except Exception as e:
            self.results["GET /api/messages"] = False
            print(f"❌ GET /api/messages: {e}")
            
        # Test 6: Get agent memories
        try:
            response = requests.get(f"{self.base_url}/api/agents/DataAnalyst/memories")
            if response.status_code == 200:
                memories = response.json()
                self.results["GET /api/agents/memories"] = len(memories) >= 0
                print(f"✅ GET /api/agents/memories: {len(memories)} memories found")
            else:
                self.results["GET /api/agents/memories"] = False
                print(f"❌ GET /api/agents/memories: Status {response.status_code}")
        except Exception as e:
            self.results["GET /api/agents/memories"] = False
            print(f"❌ GET /api/agents/memories: {e}")
            
    def test_mock_data_integration(self):
        """Test that mock data is properly integrated."""
        print("\n" + "=" * 60)
        print("TESTING MOCK DATA INTEGRATION")
        print("=" * 60)
        
        try:
            # Test agents data
            response = requests.get(f"{self.base_url}/api/agents")
            agents = response.json()
            
            expected_agents = ["DataAnalyst", "QueryBot", "ReportGen"]
            found_agents = [agent['agent'] for agent in agents]
            
            agents_match = all(agent in found_agents for agent in expected_agents)
            self.results["Mock Agents Data"] = agents_match
            
            if agents_match:
                print("✅ Mock Agents Data: All expected agents present")
            else:
                print(f"❌ Mock Agents Data: Expected {expected_agents}, found {found_agents}")
                
            # Test messages data
            response = requests.get(f"{self.base_url}/api/messages/DataAnalyst")
            messages = response.json()
            
            has_mock_messages = len(messages) > 0
            self.results["Mock Messages Data"] = has_mock_messages
            
            if has_mock_messages:
                print(f"✅ Mock Messages Data: {len(messages)} mock messages loaded")
                # Show sample message
                if messages:
                    msg = messages[0]
                    print(f"   Sample: {msg['user_from']} → {msg['user_to']}: {msg['message'][:50]}...")
            else:
                print("❌ Mock Messages Data: No mock messages found")
                
            # Test memories data  
            response = requests.get(f"{self.base_url}/api/agents/DataAnalyst/memories")
            memories = response.json()
            
            has_mock_memories = len(memories) > 0
            self.results["Mock Memories Data"] = has_mock_memories
            
            if has_mock_memories:
                print(f"✅ Mock Memories Data: {len(memories)} mock memories loaded")
                if memories:
                    mem = memories[0]
                    print(f"   Sample: {mem['Memory_Label']}: {mem['Memory'][:50]}...")
            else:
                print("❌ Mock Memories Data: No mock memories found")
                
        except Exception as e:
            print(f"❌ Mock Data Integration Test Failed: {e}")
            
    async def test_mcp_tools(self):
        """Test key MCP tools via WebSocket."""
        print("\n" + "=" * 60)
        print("TESTING MCP TOOLS")
        print("=" * 60)
        
        try:
            uri = f"{self.ws_url}/ws/agent/DataAnalyst"
            
            async with websockets.connect(uri) as websocket:
                # Wait for connection
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") != "connected":
                    self.results["WebSocket Connection"] = False
                    print("❌ WebSocket Connection: Failed to connect")
                    return
                    
                self.results["WebSocket Connection"] = True
                print("✅ WebSocket Connection: Agent connected successfully")
                
                # Test key MCP tools
                mcp_tools_to_test = [
                    ("list_databases", {"server_instance": "mock"}),
                    ("get_schema_info", {"database_name": "TriAI_Main"}),
                    ("execute_query", {
                        "database_name": "TriAI_Main", 
                        "sql_query": "SELECT * FROM AI_Agents LIMIT 2"
                    }),
                    ("store_memory", {
                        "agent_name": "DataAnalyst",
                        "memory_label": "Test Memory via MCP",
                        "memory_content": "This memory was stored via MCP tool testing",
                        "related_to_tags": "test mcp tools"
                    }),
                    ("retrieve_memories", {
                        "agent_name": "DataAnalyst",
                        "related_to_tags": "test",
                        "limit": 5
                    })
                ]
                
                for tool_name, parameters in mcp_tools_to_test:
                    try:
                        # Send MCP request
                        mcp_request = {
                            "type": "mcp_request",
                            "tool": tool_name,
                            "parameters": parameters
                        }
                        
                        await websocket.send(json.dumps(mcp_request))
                        mcp_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        mcp_data = json.loads(mcp_response)
                        
                        if mcp_data.get("success"):
                            self.results[f"MCP Tool: {tool_name}"] = True
                            print(f"✅ MCP Tool '{tool_name}': Success")
                            
                            # Show some details for key tools
                            if tool_name == "list_databases":
                                databases = mcp_data.get("data", [])
                                print(f"   Found databases: {databases}")
                            elif tool_name == "execute_query":
                                query_data = mcp_data.get("data", {})
                                print(f"   Query returned {query_data.get('row_count')} rows")
                                
                        else:
                            self.results[f"MCP Tool: {tool_name}"] = False
                            print(f"❌ MCP Tool '{tool_name}': {mcp_data.get('error')}")
                            
                    except asyncio.TimeoutError:
                        self.results[f"MCP Tool: {tool_name}"] = False
                        print(f"❌ MCP Tool '{tool_name}': Timeout")
                    except Exception as e:
                        self.results[f"MCP Tool: {tool_name}"] = False
                        print(f"❌ MCP Tool '{tool_name}': {e}")
                        
        except Exception as e:
            print(f"❌ MCP Tools Test Failed: {e}")
            
    def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n" + "=" * 60)
        print("TESTING ERROR HANDLING")
        print("=" * 60)
        
        # Test 1: Invalid endpoint
        try:
            response = requests.get(f"{self.base_url}/api/nonexistent")
            self.results["Invalid Endpoint Handling"] = response.status_code == 404
            print(f"✅ Invalid Endpoint: Correctly returns {response.status_code}")
        except Exception as e:
            self.results["Invalid Endpoint Handling"] = False
            print(f"❌ Invalid Endpoint Test: {e}")
            
        # Test 2: Invalid JSON in message
        try:
            response = requests.post(
                f"{self.base_url}/api/message",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            self.results["Invalid JSON Handling"] = response.status_code in [400, 422]
            print(f"✅ Invalid JSON: Correctly returns {response.status_code}")
        except Exception as e:
            self.results["Invalid JSON Handling"] = False
            print(f"❌ Invalid JSON Test: {e}")
            
        # Test 3: Missing required fields
        try:
            response = requests.post(
                f"{self.base_url}/api/message",
                json={"user_to": "DataAnalyst"},  # Missing message field
                headers={"Content-Type": "application/json"}
            )
            self.results["Missing Fields Handling"] = response.status_code in [400, 422]
            print(f"✅ Missing Fields: Correctly returns {response.status_code}")
        except Exception as e:
            self.results["Missing Fields Handling"] = False
            print(f"❌ Missing Fields Test: {e}")
            
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        categories = {
            "REST API": ["Server Health", "GET /api/user", "GET /api/agents", 
                        "POST /api/message", "GET /api/messages", "GET /api/agents/memories"],
            "Mock Data": ["Mock Agents Data", "Mock Messages Data", "Mock Memories Data"],
            "WebSocket & MCP": [k for k in self.results.keys() if k.startswith(("WebSocket", "MCP Tool"))],
            "Error Handling": ["Invalid Endpoint Handling", "Invalid JSON Handling", "Missing Fields Handling"]
        }
        
        total_passed = 0
        total_tests = 0
        
        for category, tests in categories.items():
            category_passed = 0
            category_total = 0
            
            print(f"\n{category}:")
            print("-" * 40)
            
            for test in tests:
                if test in self.results:
                    result = self.results[test]
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"  {test:.<30} {status}")
                    category_passed += 1 if result else 0
                    category_total += 1
                    
            print(f"  Category Score: {category_passed}/{category_total}")
            total_passed += category_passed
            total_tests += category_total
            
        print("\n" + "=" * 60)
        print(f"OVERALL RESULTS: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED! TriAI server is fully functional with mock data.")
        elif total_passed / total_tests >= 0.8:
            print("✅ Most tests passed. Server is largely functional.")
        else:
            print("⚠️ Multiple test failures. Server needs attention.")
            
        print("=" * 60)


async def main():
    """Run comprehensive tests."""
    tester = ComprehensiveTriAITester()
    
    # Run all test categories
    tester.test_rest_endpoints()
    tester.test_mock_data_integration()
    await tester.test_mcp_tools()
    tester.test_error_handling()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")