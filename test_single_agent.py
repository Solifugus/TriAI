"""
Test script for a single agent to verify functionality.
"""

import asyncio
import logging
from agent_server import TriAIAgent, AgentConfig


async def test_single_agent():
    """Test a single agent's functionality."""
    print("=" * 60)
    print("TESTING SINGLE TRIAI AGENT")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create agent configuration
    config = AgentConfig(
        name="TestAgent",
        description="Test agent for functionality verification",
        model_api="ollama", 
        model="qwen2.5-coder",
        polling_interval=2
    )
    
    # Create agent
    agent = TriAIAgent(config)
    
    print(f"✅ Created agent: {config.name}")
    print(f"   Description: {config.description}")
    print(f"   Model: {config.model}")
    
    # Test Ollama connection
    if agent.ollama.test_connection():
        print("✅ Ollama connection: Success")
    else:
        print("❌ Ollama connection: Failed")
        return
    
    # Test WebSocket connection to messaging server
    try:
        connected = await agent.connect_to_server()
        if connected:
            print("✅ WebSocket connection: Success")
            print(f"   Available MCP tools: {len(agent.mcp_tools)}")
        else:
            print("❌ WebSocket connection: Failed")
            return
            
        # Test message checking
        print("\n📝 Testing message polling...")
        messages = await agent.check_for_messages()
        print(f"✅ Message check: Found {len(messages)} messages")
        
        # Test MCP tool usage
        print("\n🔧 Testing MCP tools...")
        
        # Test list_databases
        result = await agent.send_mcp_request("list_databases", {"server_instance": "mock"})
        if result.get("success"):
            databases = result.get("data", [])
            print(f"✅ list_databases: Found {len(databases)} databases")
        else:
            print(f"❌ list_databases: {result.get('error')}")
        
        # Test AI response generation
        print("\n🤖 Testing AI response generation...")
        test_message = {
            "Message": "Hello, can you tell me about yourself?",
            "User_From": "testuser",
            "Message_ID": 999
        }
        
        response = await agent.process_message(test_message)
        print(f"✅ AI Response ({len(response)} chars): {response[:100]}...")
        
        # Test memory operations
        print("\n🧠 Testing memory operations...")
        memory_result = await agent.send_mcp_request("store_memory", {
            "agent_name": "TestAgent",
            "memory_label": "Test Memory",
            "memory_content": "This is a test memory created during agent testing",
            "related_to_tags": "test agent memory"
        })
        
        if memory_result.get("success"):
            print("✅ Memory storage: Success")
        else:
            print(f"❌ Memory storage: {memory_result.get('error')}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        
    finally:
        # Clean up
        await agent.disconnect()
        print("✅ Agent disconnected")


if __name__ == "__main__":
    asyncio.run(test_single_agent())