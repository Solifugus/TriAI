"""
Test full integration: Browser -> Messaging Server -> Agent -> Response
"""

import asyncio
import requests
import time
from agent_server import TriAIAgent, AgentConfig


async def test_full_integration():
    """Test the complete message flow."""
    print("🔄 TESTING FULL INTEGRATION")
    print("=" * 50)
    
    # Step 1: Send message via REST API (simulating browser)
    print("1️⃣ Sending message via REST API...")
    message_data = {
        "user_to": "DataAnalyst",
        "message": "Hello! Can you tell me about the available agents in the system?"
    }
    
    try:
        response = requests.post(
            "http://localhost:8080/api/message",
            json=message_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Message sent successfully")
            else:
                print(f"❌ Message failed: {result}")
                return
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return
    
    # Step 2: Start agent to process the message
    print("\n2️⃣ Starting DataAnalyst agent...")
    
    config = AgentConfig(
        name="DataAnalyst",
        description="Analyzes data and generates reports",
        model_api="ollama",
        model="qwen2.5-coder",
        polling_interval=2
    )
    
    agent = TriAIAgent(config)
    
    try:
        # Connect agent
        connected = await agent.connect_to_server()
        if not connected:
            print("❌ Agent connection failed")
            return
            
        print("✅ Agent connected successfully")
        
        # Run a few polling cycles to process messages
        print("\n3️⃣ Agent processing messages...")
        for cycle in range(3):
            print(f"   Polling cycle {cycle + 1}...")
            await agent.run_polling_cycle()
            await asyncio.sleep(3)  # Wait between cycles
        
        print("✅ Agent completed message processing")
        
    except Exception as e:
        print(f"❌ Agent error: {e}")
    finally:
        await agent.disconnect()
        print("✅ Agent disconnected")
    
    # Step 3: Check for response via REST API
    print("\n4️⃣ Checking for agent response...")
    try:
        response = requests.get("http://localhost:8080/api/messages/DataAnalyst", timeout=10)
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Retrieved {len(messages)} messages")
            
            # Look for recent agent responses
            recent_responses = [
                msg for msg in messages 
                if msg.get("user_from") == "DataAnalyst" and 
                msg.get("user_to") == "testuser"
            ]
            
            if recent_responses:
                print(f"🎉 Found {len(recent_responses)} agent responses!")
                latest = recent_responses[0]  # Most recent
                print(f"   Latest response: {latest.get('message', '')[:100]}...")
                print("\n✅ FULL INTEGRATION TEST SUCCESSFUL!")
                print("   Message flow: Browser → Server → Agent → Response ✅")
            else:
                print("⚠️ No agent responses found (may need more time)")
                
        else:
            print(f"❌ Error retrieving messages: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking messages: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Integration test completed")


if __name__ == "__main__":
    asyncio.run(test_full_integration())