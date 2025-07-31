"""
Setup PostgreSQL database for TriAI framework.
Creates database, tables, and populates with test data.
"""

import sys
import getpass
from datetime import datetime, timedelta
from pg_datalink import PostgreSQLDataLink


def create_database_and_user():
    """Create database and user for TriAI."""
    print("🐘 Setting up PostgreSQL for TriAI")
    print("=" * 40)
    
    # Get PostgreSQL admin credentials
    print("Please provide PostgreSQL admin credentials to create database and user:")
    admin_user = input("Admin username (default: postgres): ").strip() or "postgres"
    admin_password = getpass.getpass("Admin password: ")
    
    # Connect to PostgreSQL as admin
    admin_config = {
        "host": "localhost",
        "port": "5432", 
        "database": "postgres",  # Connect to default postgres database
        "user": admin_user,
        "password": admin_password
    }
    
    try:
        admin_db = PostgreSQLDataLink(admin_config, debug=True)
        
        if not admin_db.test_connection():
            print("❌ Failed to connect to PostgreSQL")
            return False
        
        print("✅ Connected to PostgreSQL as admin")
        
        # Create database
        print("\n📦 Creating TriAI database...")
        try:
            admin_db.sql_run("CREATE DATABASE triai_main")
            print("✅ Database 'triai_main' created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️ Database 'triai_main' already exists")
            else:
                print(f"❌ Error creating database: {e}")
                return False
        
        # Create user
        print("\n👤 Creating TriAI user...")
        try:
            admin_db.sql_run("CREATE USER triai_user WITH PASSWORD 'triai_password'")
            print("✅ User 'triai_user' created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️ User 'triai_user' already exists")
            else:
                print(f"❌ Error creating user: {e}")
        
        # Grant privileges
        print("\n🔐 Granting privileges...")
        admin_db.sql_run("GRANT ALL PRIVILEGES ON DATABASE triai_main TO triai_user")
        admin_db.sql_run("ALTER USER triai_user CREATEDB")  # Allow creating test databases
        print("✅ Privileges granted")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def create_tables():
    """Create TriAI tables in PostgreSQL."""
    print("\n🏗️ Creating TriAI tables...")
    
    # Connect to TriAI database
    triai_config = {
        "host": "localhost",
        "port": "5432",
        "database": "triai_main", 
        "user": "triai_user",
        "password": "triai_password"
    }
    
    db = PostgreSQLDataLink(triai_config, debug=True)
    
    if not db.test_connection():
        print("❌ Failed to connect to TriAI database")
        return False
    
    print("✅ Connected to TriAI database")
    
    # Table creation SQL (adapted for PostgreSQL)
    tables = {
        "AI_Agents": """
            CREATE TABLE IF NOT EXISTS AI_Agents (
                Agent VARCHAR(15) PRIMARY KEY,
                Description TEXT,
                Model_API VARCHAR(30),
                Model VARCHAR(100),
                Model_API_KEY VARCHAR(500)
            )
        """,
        
        "AI_Messages": """
            CREATE TABLE IF NOT EXISTS AI_Messages (
                Message_ID SERIAL PRIMARY KEY,
                Posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                User_From VARCHAR(15) NOT NULL,
                User_To VARCHAR(15) NOT NULL,
                Message TEXT,
                User_Read TIMESTAMP
            )
        """,
        
        "AI_Memories": """
            CREATE TABLE IF NOT EXISTS AI_Memories (
                Memory_ID SERIAL PRIMARY KEY,
                Agent VARCHAR(15) NOT NULL,
                First_Posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Times_Recalled INTEGER DEFAULT 0,
                Last_Recalled TIMESTAMP,
                Memory_Label VARCHAR(100) NOT NULL,
                Memory TEXT,
                Related_To VARCHAR(200) NOT NULL,
                Purge_After TIMESTAMP,
                FOREIGN KEY (Agent) REFERENCES AI_Agents(Agent)
            )
        """,
        
        "AI_Query_History": """
            CREATE TABLE IF NOT EXISTS AI_Query_History (
                Query_ID SERIAL PRIMARY KEY,
                Agent VARCHAR(30) NOT NULL,
                Database_Name VARCHAR(100),
                SQL_Query TEXT,
                Executed_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Row_Count INTEGER,
                Execution_Time_MS INTEGER,
                FOREIGN KEY (Agent) REFERENCES AI_Agents(Agent)
            )
        """
    }
    
    # Create tables
    for table_name, sql in tables.items():
        try:
            print(f"   Creating {table_name}...")
            db.sql_run(sql)
            print(f"   ✅ {table_name} created")
        except Exception as e:
            print(f"   ❌ Error creating {table_name}: {e}")
            return False
    
    print("✅ All tables created successfully")
    return True


def populate_test_data():
    """Populate tables with test data."""
    print("\n📊 Populating with test data...")
    
    triai_config = {
        "host": "localhost",
        "port": "5432",
        "database": "triai_main",
        "user": "triai_user", 
        "password": "triai_password"
    }
    
    db = PostgreSQLDataLink(triai_config, debug=True)
    
    # Test data
    agents_data = [
        {
            "Agent": "DataAnalyst",
            "Description": "Analyzes data and generates reports using advanced analytics",
            "Model_API": "ollama",
            "Model": "qwen2.5-coder",
            "Model_API_KEY": None
        },
        {
            "Agent": "QueryBot",
            "Description": "Executes database queries and explains results in plain language",
            "Model_API": "ollama",
            "Model": "qwen2.5-coder", 
            "Model_API_KEY": None
        },
        {
            "Agent": "ReportGen",
            "Description": "Generates comprehensive business reports from data analysis",
            "Model_API": "ollama",
            "Model": "qwen2.5-coder",
            "Model_API_KEY": None
        }
    ]
    
    messages_data = [
        {
            "Posted": datetime.now() - timedelta(hours=2),
            "User_From": "testuser",
            "User_To": "DataAnalyst",
            "Message": "Can you analyze the sales data for last quarter?",
            "User_Read": None
        },
        {
            "Posted": datetime.now() - timedelta(hours=1, minutes=45),
            "User_From": "DataAnalyst",
            "User_To": "testuser",
            "Message": "I'll analyze the Q3 sales data for you. Let me query the database and generate a comprehensive report.",
            "User_Read": datetime.now() - timedelta(hours=1, minutes=30)
        },
        {
            "Posted": datetime.now() - timedelta(minutes=30),
            "User_From": "testuser",
            "User_To": "QueryBot",
            "Message": "Show me all customers from California",
            "User_Read": None
        },
        {
            "Posted": datetime.now() - timedelta(minutes=25),
            "User_From": "QueryBot",
            "User_To": "testuser", 
            "Message": "Here are the California customers from our database:\n\n| Customer | City | Orders |\n|----------|------|--------|\n| Acme Corp | Los Angeles | 15 |\n| TechStart Inc | San Francisco | 8 |",
            "User_Read": None
        }
    ]
    
    memories_data = [
        {
            "Agent": "DataAnalyst",
            "First_Posted": datetime.now() - timedelta(days=5),
            "Times_Recalled": 3,
            "Last_Recalled": datetime.now() - timedelta(hours=6),
            "Memory_Label": "Q3 Sales Analysis Preferences",
            "Memory": "User prefers quarterly sales analysis with trend comparison, regional breakdown, and executive summary format.",
            "Related_To": "sales analysis quarterly trends reporting",
            "Purge_After": None
        },
        {
            "Agent": "QueryBot",
            "First_Posted": datetime.now() - timedelta(days=2),
            "Times_Recalled": 1,
            "Last_Recalled": datetime.now() - timedelta(hours=12),
            "Memory_Label": "Customer Query Patterns",
            "Memory": "User frequently asks for customer data filtered by geographic regions, especially California and Texas.",
            "Related_To": "customers geography filters queries",
            "Purge_After": None
        },
        {
            "Agent": "ReportGen",
            "First_Posted": datetime.now() - timedelta(days=1),
            "Times_Recalled": 0,
            "Last_Recalled": None,
            "Memory_Label": "Report Format Preferences", 
            "Memory": "User prefers reports with executive summary, detailed analysis, charts, and actionable recommendations.",
            "Related_To": "reports format structure recommendations",
            "Purge_After": None
        }
    ]
    
    query_history_data = [
        {
            "Agent": "DataAnalyst",
            "Database_Name": "triai_main",
            "SQL_Query": "SELECT COUNT(*) as total_agents FROM AI_Agents",
            "Executed_Time": datetime.now() - timedelta(hours=3),
            "Row_Count": 1,
            "Execution_Time_MS": 45
        },
        {
            "Agent": "QueryBot",
            "Database_Name": "triai_main", 
            "SQL_Query": "SELECT Agent, Description FROM AI_Agents WHERE Model_API = 'ollama'",
            "Executed_Time": datetime.now() - timedelta(minutes=45),
            "Row_Count": 3,
            "Execution_Time_MS": 89
        }
    ]
    
    # Insert test data
    try:
        print("   Inserting agents...")
        db.sql_insert("AI_Agents", agents_data)
        print("   ✅ Agents inserted")
        
        print("   Inserting messages...")
        db.sql_insert("AI_Messages", messages_data)
        print("   ✅ Messages inserted")
        
        print("   Inserting memories...")
        db.sql_insert("AI_Memories", memories_data)
        print("   ✅ Memories inserted")
        
        print("   Inserting query history...")
        db.sql_insert("AI_Query_History", query_history_data)
        print("   ✅ Query history inserted")
        
        print("✅ All test data inserted successfully")
        
        # Verify data
        print("\n🔍 Verifying data...")
        agents_count = db.sql_get("SELECT COUNT(*) as count FROM AI_Agents")[0]['count']
        messages_count = db.sql_get("SELECT COUNT(*) as count FROM AI_Messages")[0]['count']
        memories_count = db.sql_get("SELECT COUNT(*) as count FROM AI_Memories")[0]['count']
        
        print(f"   📊 Data summary:")
        print(f"   - Agents: {agents_count}")
        print(f"   - Messages: {messages_count}")
        print(f"   - Memories: {memories_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inserting test data: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 TriAI PostgreSQL Setup")
    print("=" * 30)
    
    try:
        # Step 1: Create database and user
        if not create_database_and_user():
            print("❌ Failed to create database and user")
            return 1
        
        # Step 2: Create tables
        if not create_tables():
            print("❌ Failed to create tables")
            return 1
        
        # Step 3: Populate test data
        if not populate_test_data():
            print("❌ Failed to populate test data")
            return 1
        
        print("\n🎉 PostgreSQL setup completed successfully!")
        print("\n📋 Connection details:")
        print("   Host: localhost")
        print("   Port: 5432")
        print("   Database: triai_main")
        print("   User: triai_user")
        print("   Password: triai_password")
        
        print("\n🔧 Next steps:")
        print("   1. Update config.yaml to use PostgreSQL")
        print("   2. Restart TriAI messaging server")
        print("   3. Test with real database!")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())