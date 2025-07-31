"""
Automated PostgreSQL setup for TriAI framework.
Uses peer authentication to avoid password prompts.
"""

import subprocess
import sys
from datetime import datetime, timedelta
from pg_datalink import PostgreSQLDataLink


def run_psql_command(command, database="postgres"):
    """Run a psql command using peer authentication."""
    try:
        cmd = ["psql", "-d", database, "-c", command]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def setup_database():
    """Setup database and user using psql commands."""
    print("🐘 Setting up PostgreSQL for TriAI")
    print("=" * 40)
    
    # Try to connect using current user (peer authentication)
    success, stdout, stderr = run_psql_command("SELECT version();")
    
    if not success:
        print("❌ Cannot connect to PostgreSQL.")
        print("   Make sure PostgreSQL is running and you have access.")
        print("   You may need to run: sudo -u postgres python setup_postgres_auto.py")
        return False
    
    print("✅ Connected to PostgreSQL")
    
    # Create database
    print("\n📦 Creating TriAI database...")
    success, stdout, stderr = run_psql_command("CREATE DATABASE triai_main;")
    
    if success or "already exists" in stderr.lower():
        print("✅ Database 'triai_main' ready")
    else:
        print(f"❌ Error creating database: {stderr}")
        return False
    
    # Create user
    print("\n👤 Creating TriAI user...")
    success, stdout, stderr = run_psql_command("CREATE USER triai_user WITH PASSWORD 'triai_password';")
    
    if success or "already exists" in stderr.lower():
        print("✅ User 'triai_user' ready") 
    else:
        print(f"❌ Error creating user: {stderr}")
    
    # Grant privileges
    print("\n🔐 Granting privileges...")
    run_psql_command("GRANT ALL PRIVILEGES ON DATABASE triai_main TO triai_user;")
    run_psql_command("ALTER USER triai_user CREATEDB;")
    
    # Grant schema privileges
    run_psql_command("GRANT ALL ON SCHEMA public TO triai_user;", "triai_main")
    run_psql_command("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO triai_user;", "triai_main")
    run_psql_command("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO triai_user;", "triai_main")
    
    print("✅ Privileges granted")
    return True


def create_tables():
    """Create TriAI tables using psql commands."""
    print("\n🏗️ Creating TriAI tables...")
    
    tables_sql = """
    -- AI Agents table
    CREATE TABLE IF NOT EXISTS AI_Agents (
        Agent VARCHAR(15) PRIMARY KEY,
        Description TEXT,
        Model_API VARCHAR(30),
        Model VARCHAR(100),
        Model_API_KEY VARCHAR(500)
    );
    
    -- AI Messages table
    CREATE TABLE IF NOT EXISTS AI_Messages (
        Message_ID SERIAL PRIMARY KEY,
        Posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        User_From VARCHAR(15) NOT NULL,
        User_To VARCHAR(15) NOT NULL,
        Message TEXT,
        User_Read TIMESTAMP
    );
    
    -- AI Memories table
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
    );
    
    -- AI Query History table
    CREATE TABLE IF NOT EXISTS AI_Query_History (
        Query_ID SERIAL PRIMARY KEY,
        Agent VARCHAR(30) NOT NULL,
        Database_Name VARCHAR(100),
        SQL_Query TEXT,
        Executed_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        Row_Count INTEGER,
        Execution_Time_MS INTEGER,
        FOREIGN KEY (Agent) REFERENCES AI_Agents(Agent)
    );
    """
    
    # Write SQL to temp file and execute
    with open("/tmp/triai_schema.sql", "w") as f:
        f.write(tables_sql)
    
    cmd = ["psql", "-d", "triai_main", "-f", "/tmp/triai_schema.sql"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ All tables created successfully")
        return True
    else:
        print(f"❌ Error creating tables: {result.stderr}")
        return False


def populate_test_data():
    """Populate tables with test data using psql."""
    print("\n📊 Populating with test data...")
    
    data_sql = """
    -- Insert agents
    INSERT INTO AI_Agents (Agent, Description, Model_API, Model) VALUES
    ('DataAnalyst', 'Analyzes data and generates reports using advanced analytics', 'ollama', 'qwen2.5-coder'),
    ('QueryBot', 'Executes database queries and explains results in plain language', 'ollama', 'qwen2.5-coder'),
    ('ReportGen', 'Generates comprehensive business reports from data analysis', 'ollama', 'qwen2.5-coder')
    ON CONFLICT (Agent) DO NOTHING;
    
    -- Insert sample messages
    INSERT INTO AI_Messages (Posted, User_From, User_To, Message, User_Read) VALUES
    (NOW() - INTERVAL '2 hours', 'testuser', 'DataAnalyst', 'Can you analyze the sales data for last quarter?', NULL),
    (NOW() - INTERVAL '1 hour 45 minutes', 'DataAnalyst', 'testuser', 'I''ll analyze the Q3 sales data for you. Let me query the database and generate a comprehensive report.', NOW() - INTERVAL '1 hour 30 minutes'),
    (NOW() - INTERVAL '30 minutes', 'testuser', 'QueryBot', 'Show me all customers from California', NULL),
    (NOW() - INTERVAL '25 minutes', 'QueryBot', 'testuser', 'Here are the California customers from our database: We have several major clients including Acme Corp in Los Angeles and TechStart Inc in San Francisco.', NULL);
    
    -- Insert sample memories
    INSERT INTO AI_Memories (Agent, First_Posted, Times_Recalled, Last_Recalled, Memory_Label, Memory, Related_To) VALUES
    ('DataAnalyst', NOW() - INTERVAL '5 days', 3, NOW() - INTERVAL '6 hours', 'Q3 Sales Analysis Preferences', 'User prefers quarterly sales analysis with trend comparison, regional breakdown, and executive summary format.', 'sales analysis quarterly trends reporting'),
    ('QueryBot', NOW() - INTERVAL '2 days', 1, NOW() - INTERVAL '12 hours', 'Customer Query Patterns', 'User frequently asks for customer data filtered by geographic regions, especially California and Texas.', 'customers geography filters queries'),
    ('ReportGen', NOW() - INTERVAL '1 day', 0, NULL, 'Report Format Preferences', 'User prefers reports with executive summary, detailed analysis, charts, and actionable recommendations.', 'reports format structure recommendations');
    
    -- Insert sample query history
    INSERT INTO AI_Query_History (Agent, Database_Name, SQL_Query, Executed_Time, Row_Count, Execution_Time_MS) VALUES
    ('DataAnalyst', 'triai_main', 'SELECT COUNT(*) as total_agents FROM AI_Agents', NOW() - INTERVAL '3 hours', 1, 45),
    ('QueryBot', 'triai_main', 'SELECT Agent, Description FROM AI_Agents WHERE Model_API = ''ollama''', NOW() - INTERVAL '45 minutes', 3, 89);
    """
    
    # Write SQL to temp file and execute
    with open("/tmp/triai_data.sql", "w") as f:
        f.write(data_sql)
    
    cmd = ["psql", "-d", "triai_main", "-f", "/tmp/triai_data.sql"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Test data inserted successfully")
        
        # Verify data
        print("\n🔍 Verifying data...")
        cmd = ["psql", "-d", "triai_main", "-t", "-c", "SELECT COUNT(*) FROM AI_Agents;"]
        agents_result = subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = ["psql", "-d", "triai_main", "-t", "-c", "SELECT COUNT(*) FROM AI_Messages;"]
        messages_result = subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = ["psql", "-d", "triai_main", "-t", "-c", "SELECT COUNT(*) FROM AI_Memories;"]
        memories_result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"   📊 Data summary:")
        print(f"   - Agents: {agents_result.stdout.strip()}")
        print(f"   - Messages: {messages_result.stdout.strip()}")
        print(f"   - Memories: {memories_result.stdout.strip()}")
        
        return True
    else:
        print(f"❌ Error inserting test data: {result.stderr}")
        return False


def test_connection():
    """Test the PostgreSQL DataLink connection."""
    print("\n🧪 Testing PostgreSQL DataLink...")
    
    config = {
        "host": "localhost",
        "port": "5432",
        "database": "triai_main",
        "user": "triai_user",
        "password": "triai_password"
    }
    
    try:
        db = PostgreSQLDataLink(config, debug=True)
        
        if db.test_connection():
            print("✅ DataLink connection successful")
            
            # Test a simple query
            agents = db.sql_get("SELECT Agent, Description FROM AI_Agents LIMIT 2")
            print(f"✅ Query test: Retrieved {len(agents)} agents")
            
            for agent in agents:
                print(f"   - {agent['agent']}: {agent['description'][:50]}...")
                
            return True
        else:
            print("❌ DataLink connection failed")
            return False
            
    except Exception as e:
        print(f"❌ DataLink test error: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 TriAI PostgreSQL Automated Setup")
    print("=" * 40)
    
    try:
        # Step 1: Setup database and user
        if not setup_database():
            print("❌ Failed to setup database")
            return 1
        
        # Step 2: Create tables
        if not create_tables():
            print("❌ Failed to create tables")
            return 1
        
        # Step 3: Populate test data
        if not populate_test_data():
            print("❌ Failed to populate test data")
            return 1
        
        # Step 4: Test connection
        if not test_connection():
            print("❌ Failed connection test")
            return 1
        
        print("\n🎉 PostgreSQL setup completed successfully!")
        print("\n📋 Connection details:")
        print("   Host: localhost")
        print("   Port: 5432")
        print("   Database: triai_main")
        print("   User: triai_user")
        print("   Password: triai_password")
        
        print("\n🔧 Next steps:")
        print("   1. Update config.yaml to use PostgreSQL:")
        print("      server:")
        print("        use_mock_db: false")
        print("      database:")
        print("        type: postgresql")
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