"""
Working PostgreSQL setup for TriAI using Unix socket connection.
"""

import subprocess
from pg_datalink import PostgreSQLDataLink


def main():
    print("🐘 TriAI PostgreSQL Setup (Working Version)")
    print("=" * 50)
    
    # Working configuration using Unix socket
    config = {
        "host": "/var/run/postgresql",
        "port": "5432",
        "database": "postgres", 
        "user": "solifugus",
        "password": ""
    }
    
    print("1️⃣ Testing PostgreSQL connection...")
    db = PostgreSQLDataLink(config, debug=True)
    
    if not db.test_connection():
        print("❌ Cannot connect to PostgreSQL")
        return 1
        
    print("✅ Connected to PostgreSQL successfully")
    
    # Create TriAI database
    print("\n2️⃣ Creating TriAI database...")
    try:
        db.sql_run("CREATE DATABASE triai_main")
        print("✅ Database created")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("ℹ️ Database already exists")
        else:
            print(f"❌ Error: {e}")
            return 1
    
    # Connect to TriAI database
    print("\n3️⃣ Connecting to TriAI database...")
    triai_config = {
        "host": "/var/run/postgresql",
        "port": "5432",
        "database": "triai_main",
        "user": "solifugus", 
        "password": ""
    }
    
    triai_db = PostgreSQLDataLink(triai_config, debug=True)
    
    if not triai_db.test_connection():
        print("❌ Cannot connect to TriAI database")
        return 1
        
    print("✅ Connected to TriAI database")
    
    # Create tables
    print("\n4️⃣ Creating tables...")
    tables = [
        """
        CREATE TABLE IF NOT EXISTS AI_Agents (
            Agent VARCHAR(15) PRIMARY KEY,
            Description TEXT,
            Model_API VARCHAR(30),
            Model VARCHAR(100),
            Model_API_KEY VARCHAR(500)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS AI_Messages (
            Message_ID SERIAL PRIMARY KEY,
            Posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            User_From VARCHAR(15) NOT NULL,
            User_To VARCHAR(15) NOT NULL,
            Message TEXT,
            User_Read TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS AI_Memories (
            Memory_ID SERIAL PRIMARY KEY,
            Agent VARCHAR(15) NOT NULL,
            First_Posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            Times_Recalled INTEGER DEFAULT 0,
            Last_Recalled TIMESTAMP,
            Memory_Label VARCHAR(100) NOT NULL,
            Memory TEXT,
            Related_To VARCHAR(200) NOT NULL,
            Purge_After TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS AI_Query_History (
            Query_ID SERIAL PRIMARY KEY,
            Agent VARCHAR(30) NOT NULL,
            Database_Name VARCHAR(100),
            SQL_Query TEXT,
            Executed_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            Row_Count INTEGER,
            Execution_Time_MS INTEGER
        )
        """
    ]
    
    for i, table_sql in enumerate(tables, 1):
        try:
            triai_db.sql_run(table_sql)
            print(f"   ✅ Table {i}/4 created")
        except Exception as e:
            print(f"   ❌ Error creating table {i}: {e}")
    
    # Populate with test data
    print("\n5️⃣ Adding test data...")
    
    # Agents
    agents_data = [
        {
            "Agent": "DataAnalyst",
            "Description": "Analyzes data and generates reports using advanced analytics",
            "Model_API": "ollama",
            "Model": "qwen2.5-coder"
        },
        {
            "Agent": "QueryBot", 
            "Description": "Executes database queries and explains results in plain language",
            "Model_API": "ollama",
            "Model": "qwen2.5-coder"
        },
        {
            "Agent": "ReportGen",
            "Description": "Generates comprehensive business reports from data analysis",
            "Model_API": "ollama",
            "Model": "qwen2.5-coder"
        }
    ]
    
    try:
        # Clear existing data first
        triai_db.sql_run("DELETE FROM AI_Query_History")
        triai_db.sql_run("DELETE FROM AI_Memories") 
        triai_db.sql_run("DELETE FROM AI_Messages")
        triai_db.sql_run("DELETE FROM AI_Agents")
        
        # Insert agents
        triai_db.sql_insert("AI_Agents", agents_data)
        print("   ✅ Agents added")
        
        # Add sample messages
        messages_data = [
            {
                "User_From": "testuser",
                "User_To": "DataAnalyst", 
                "Message": "Can you analyze the sales data for last quarter?",
                "Posted": "2025-07-24 19:00:00"
            },
            {
                "User_From": "DataAnalyst",
                "User_To": "testuser",
                "Message": "I'll help you analyze the Q3 sales data. Let me query the database and generate a comprehensive report with trends and insights.",
                "Posted": "2025-07-24 19:01:00"
            },
            {
                "User_From": "testuser", 
                "User_To": "QueryBot",
                "Message": "Show me information about the available AI agents",
                "Posted": "2025-07-24 20:00:00"
            }
        ]
        
        triai_db.sql_insert("AI_Messages", messages_data)
        print("   ✅ Messages added")
        
        # Add sample memories
        memories_data = [
            {
                "Agent": "DataAnalyst",
                "Memory_Label": "Sales Analysis Preferences",
                "Memory": "User prefers quarterly sales analysis with trend comparison and regional breakdown",
                "Related_To": "sales analysis quarterly trends",
                "Times_Recalled": 2
            },
            {
                "Agent": "QueryBot",
                "Memory_Label": "Query Patterns", 
                "Memory": "User often asks for information about system agents and database structure",
                "Related_To": "agents database queries system",
                "Times_Recalled": 1
            }
        ]
        
        triai_db.sql_insert("AI_Memories", memories_data)
        print("   ✅ Memories added")
        
    except Exception as e:
        print(f"   ❌ Error adding test data: {e}")
    
    # Verify setup
    print("\n6️⃣ Verifying setup...")
    try:
        agents = triai_db.sql_get("SELECT COUNT(*) as count FROM AI_Agents")
        messages = triai_db.sql_get("SELECT COUNT(*) as count FROM AI_Messages") 
        memories = triai_db.sql_get("SELECT COUNT(*) as count FROM AI_Memories")
        
        print(f"   📊 Data counts:")
        print(f"   - Agents: {agents[0]['count']}")
        print(f"   - Messages: {messages[0]['count']}")
        print(f"   - Memories: {memories[0]['count']}")
        
        # Test a sample query
        agent_list = triai_db.sql_get("SELECT Agent, Description FROM AI_Agents")
        print(f"\n   🤖 Available agents:")
        for agent in agent_list:
            print(f"   - {agent['agent']}: {agent['description'][:50]}...")
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return 1
    
    print("\n🎉 PostgreSQL setup completed successfully!")
    print("\n📋 Connection details for TriAI:")
    print("   Host: /var/run/postgresql")
    print("   Port: 5432")
    print("   Database: triai_main")
    print("   User: solifugus")
    print("   Password: (none - using peer auth)")
    
    print("\n🔧 Configuration for config.yaml:")
    print("   database:")
    print("     type: postgresql")
    print("     host: /var/run/postgresql")
    print("     port: 5432")
    print("     database: triai_main")
    print("     user: solifugus")
    print("     password: ''")
    
    return 0


if __name__ == "__main__":
    exit(main())