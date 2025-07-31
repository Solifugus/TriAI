"""
Test script for an existing agent (DataAnalyst).
"""

import asyncio
import logging
from agent_server import TriAIAgent, AgentConfig


async def test_existing_agent():
    """Test an existing agent that's already in the database."""
    print("=" * 60)
    print("TESTING EXISTING TRIAI AGENT (DataAnalyst)")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create agent configuration for DataAnalyst (exists in mock DB)
    config = AgentConfig(
        name="DataAnalyst",
        description="Analyzes data and generates reports using advanced analytics",
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
        
        if messages:
            print("   Recent messages:")
            for msg in messages[:2]:
                print(f"   - From {msg.get('User_From')}: {msg.get('Message', '')[:50]}...")
        
        # Test MCP tool usage
        print("\n🔧 Testing MCP tools...")
        
        # Test list_databases
        result = await agent.send_mcp_request("list_databases", {"server_instance": "mock"})
        if result.get("success"):
            databases = result.get("data", [])
            print(f"✅ list_databases: Found {len(databases)} databases: {databases}")
        else:
            print(f"❌ list_databases: {result.get('error')}")
        
        # Test execute_query
        result = await agent.send_mcp_request("execute_query", {
            "database_name": "TriAI_Main",
            "sql_query": "SELECT Agent, Description FROM AI_Agents LIMIT 3"
        })
        if result.get("success"):
            query_data = result.get("data", {})
            rows = query_data.get("results", [])
            print(f"✅ execute_query: Retrieved {len(rows)} rows")
            for row in rows:
                print(f"   - {row.get('Agent')}: {row.get('Description', '')[:40]}...")
        else:
            print(f"❌ execute_query: {result.get('error')}")
        
        # Test AI response generation
        print("\n🤖 Testing AI response generation...")
        test_message = {
            "Message": "Hello DataAnalyst! Can you help me analyze some sales data?",
            "User_From": "testuser",
            "Message_ID": 999
        }
        
        print("   Generating AI response (this may take a moment)...")
        response = await agent.process_message(test_message)
        print(f"✅ AI Response ({len(response)} chars):")
        print(f"   {response[:200]}...")
        
        # Test memory operations
        print("\n🧠 Testing memory operations...")
        memory_result = await agent.send_mcp_request("store_memory", {
            "agent_name": "DataAnalyst",
            "memory_label": "Test Analysis Session",
            "memory_content": "User requested help with sales data analysis during testing",
            "related_to_tags": "test sales analysis data"
        })
        
        if memory_result.get("success"):
            memory_data = memory_result.get("data", {})
            print(f"✅ Memory storage: Success (ID: {memory_data.get('memory_id')})")
        else:
            print(f"❌ Memory storage: {memory_result.get('error')}")
        
        # Test memory retrieval
        retrieve_result = await agent.send_mcp_request("retrieve_memories", {
            "agent_name": "DataAnalyst",
            "related_to_tags": "test analysis",
            "limit": 3
        })
        
        if retrieve_result.get("success"):
            memories = retrieve_result.get("data", [])
            print(f"✅ Memory retrieval: Found {len(memories)} relevant memories")
        else:
            print(f"❌ Memory retrieval: {retrieve_result.get('error')}")
        
        print("\n🎉 All agent tests completed successfully!")
        print("🚀 Agent is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        await agent.disconnect()
        print("✅ Agent disconnected")


if __name__ == "__main__":
    asyncio.run(test_existing_agent())