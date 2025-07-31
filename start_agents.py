"""
Start script for TriAI agents.
"""

import asyncio
import signal
import sys
from agent_server import AgentManager


async def main():
    """Start the agent manager."""
    print("🚀 Starting TriAI Agent Server")
    print("=" * 40)
    
    manager = AgentManager()
    
    def signal_handler(signum, frame):
        print("\n🛑 Shutdown signal received")
        sys.exit(0)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await manager.run()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("👋 Agent server stopped")


if __name__ == "__main__":
    asyncio.run(main())