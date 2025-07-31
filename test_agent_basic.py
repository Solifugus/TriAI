"""
Basic test for agent server functionality.
"""

import asyncio
import logging
import time
from agent_server import TriAIAgent, AgentConfig


async def test_agent_basic():
    """Basic test of agent functionality."""
    print("=" * 50)
    print("BASIC AGENT TEST")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent
    config = AgentConfig(
        name="DataAnalyst",
        description="Test agent",
        model_api="ollama",
        model="qwen2.5-coder"
    )
    
    agent = TriAIAgent(config)
    print(f"✅ Agent created: {config.name}")
    
    # Test Ollama
    if agent.ollama.test_connection():
        print("✅ Ollama: Connected")
        
        # Quick generation test
        try:
            response = await agent.ollama.generate(
                model="qwen2.5-coder",
                prompt="Say hello in one sentence."
            )
            print(f"✅ Ollama generation: {response[:50]}...")
        except Exception as e:
            print(f"❌ Ollama generation: {e}")
    else:
        print("❌ Ollama: Not available")
        return
    
    # Test WebSocket connection
    try:
        print("🔌 Connecting to messaging server...")
        connected = await asyncio.wait_for(agent.connect_to_server(), timeout=10)
        
        if connected:
            print("✅ WebSocket: Connected")
            print(f"   MCP tools available: {len(agent.mcp_tools)}")
            
            # Quick message check (non-blocking)
            try:
                print("📝 Checking for messages...")
                check_task = asyncio.create_task(agent.check_for_messages())
                messages = await asyncio.wait_for(check_task, timeout=5)
                print(f"✅ Message check: {len(messages)} messages found")
                
            except asyncio.TimeoutError:
                print("⚠️ Message check: Timeout (normal for testing)")
            except Exception as e:
                print(f"❌ Message check: {e}")
            
            # Test one MCP tool quickly
            try:
                print("🔧 Testing MCP tool...")
                tool_task = asyncio.create_task(
                    agent.send_mcp_request("list_databases", {"server_instance": "mock"})
                )
                result = await asyncio.wait_for(tool_task, timeout=10)
                
                if result.get("success"):
                    print(f"✅ MCP tool: Success - {result.get('data', [])}")
                else:
                    print(f"❌ MCP tool: {result.get('error')}")
                    
            except asyncio.TimeoutError:
                print("⚠️ MCP tool: Timeout")
            except Exception as e:
                print(f"❌ MCP tool: {e}")
            
        else:
            print("❌ WebSocket: Connection failed")
            
    except asyncio.TimeoutError:
        print("❌ WebSocket: Connection timeout")
    except Exception as e:
        print(f"❌ WebSocket: {e}")
    
    finally:
        await agent.disconnect()
        print("✅ Agent disconnected")
    
    print("\n🎯 BASIC TEST COMPLETED")
    print("   If WebSocket and Ollama both work, the agent is functional!")


if __name__ == "__main__":
    asyncio.run(test_agent_basic())