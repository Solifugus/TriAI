"""
Test script for the TriAI messaging server.
Tests REST API endpoints and basic functionality.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any

import requests
import websockets


class TriAIServerTester:
    """Test class for TriAI messaging server."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize tester with server base URL."""
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        
    def test_server_health(self) -> bool:
        """Test if server is running and responsive."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Server health check failed: {str(e)}")
            return False
    
    def test_get_user(self) -> bool:
        """Test GET /api/user endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/user")
            
            if response.status_code == 200:
                data = response.json()
                if "username" in data:
                    print(f"✅ GET /api/user: {data['username']}")
                    return True
                else:
                    print("❌ GET /api/user: Missing username field")
                    return False
            else:
                print(f"❌ GET /api/user: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ GET /api/user failed: {str(e)}")
            return False
    
    def test_get_agents(self) -> bool:
        """Test GET /api/agents endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/agents")
            
            if response.status_code == 200:
                agents = response.json()
                print(f"✅ GET /api/agents: Found {len(agents)} agents")
                
                for agent in agents[:3]:  # Show first 3 agents
                    print(f"   - {agent['agent']}: {agent['description']}")
                    
                return True
            else:
                print(f"❌ GET /api/agents: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ GET /api/agents failed: {str(e)}")
            return False
    
    def test_send_message(self) -> bool:
        """Test POST /api/message endpoint."""
        try:
            message_data = {
                "user_to": "DataAnalyst",
                "message": "This is a test message from the test script"
            }
            
            response = requests.post(
                f"{self.base_url}/api/message",
                json=message_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ POST /api/message: Message sent successfully")
                    return True
                else:
                    print(f"❌ POST /api/message: {result}")
                    return False
            else:
                print(f"❌ POST /api/message: Status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ POST /api/message failed: {str(e)}")
            return False
    
    def test_get_messages(self) -> bool:
        """Test GET /api/messages/{agent} endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/messages/DataAnalyst")
            
            if response.status_code == 200:
                messages = response.json()
                print(f"✅ GET /api/messages/DataAnalyst: Found {len(messages)} messages")
                
                # Show recent messages
                for message in messages[:2]:
                    timestamp = message['posted'][:19] if len(message['posted']) > 19 else message['posted']
                    print(f"   [{timestamp}] {message['user_from']} → {message['user_to']}: {message['message'][:50]}...")
                    
                return True
            else:
                print(f"❌ GET /api/messages/DataAnalyst: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ GET /api/messages failed: {str(e)}")
            return False
    
    def test_api_docs(self) -> bool:
        """Test API documentation endpoints."""
        try:
            # Test Swagger UI
            swagger_response = requests.get(f"{self.base_url}/docs")
            redoc_response = requests.get(f"{self.base_url}/redoc")
            
            swagger_ok = swagger_response.status_code == 200
            redoc_ok = redoc_response.status_code == 200
            
            if swagger_ok and redoc_ok:
                print("✅ API documentation: Both Swagger UI and ReDoc accessible")
                return True
            else:
                print(f"❌ API documentation: Swagger: {swagger_response.status_code}, ReDoc: {redoc_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API documentation test failed: {str(e)}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection for agents."""
        try:
            uri = f"{self.ws_url}/ws/agent/DataAnalyst"
            
            async with websockets.connect(uri) as websocket:
                # Wait for connection confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "connected":
                    print(f"✅ WebSocket connection: Agent {data.get('agent_name')} connected")
                    
                    # Test MCP tool request
                    mcp_request = {
                        "type": "mcp_request",
                        "tool": "list_databases",
                        "parameters": {"server_instance": "mock"}
                    }
                    
                    await websocket.send(json.dumps(mcp_request))
                    
                    # Wait for MCP response
                    mcp_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    mcp_data = json.loads(mcp_response)
                    
                    if mcp_data.get("success"):
                        print("✅ WebSocket MCP tool: list_databases executed successfully")
                        return True
                    else:
                        print(f"❌ WebSocket MCP tool failed: {mcp_data.get('error')}")
                        return False
                else:
                    print(f"❌ WebSocket connection failed: {data}")
                    return False
                    
        except asyncio.TimeoutError:
            print("❌ WebSocket test timed out")
            return False
        except Exception as e:
            print(f"❌ WebSocket test failed: {str(e)}")
            return False
    
    def run_rest_tests(self) -> Dict[str, bool]:
        """Run all REST API tests."""
        print("=" * 50)
        print("Testing TriAI Messaging Server REST API")
        print("=" * 50)
        
        tests = {
            "Server Health": self.test_server_health(),
            "GET /api/user": self.test_get_user(),
            "GET /api/agents": self.test_get_agents(),
            "POST /api/message": self.test_send_message(),
            "GET /api/messages": self.test_get_messages(),
            "API Documentation": self.test_api_docs()
        }
        
        return tests
    
    async def run_websocket_tests(self) -> Dict[str, bool]:
        """Run WebSocket tests."""
        print("\n" + "=" * 50)
        print("Testing TriAI Messaging Server WebSocket")
        print("=" * 50)
        
        tests = {
            "WebSocket Connection & MCP": await self.test_websocket_connection()
        }
        
        return tests


async def main():
    """Run all tests."""
    tester = TriAIServerTester()
    
    # Run REST API tests
    rest_results = tester.run_rest_tests()
    
    # Run WebSocket tests
    ws_results = await tester.run_websocket_tests()
    
    # Combine results
    all_results = {**rest_results, **ws_results}
    
    # Print summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for result in all_results.values() if result)
    total = len(all_results)
    
    for test_name, result in all_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Server is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check server logs for details.")
        return 1


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)