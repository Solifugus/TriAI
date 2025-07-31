"""
Simple PostgreSQL test for TriAI.
"""

from pg_datalink import PostgreSQLDataLink


def main():
    print("🐘 Simple PostgreSQL Test")
    print("=" * 30)
    
    # Try different connection methods
    configs_to_try = [
        {
            "host": "localhost",
            "port": "5432",
            "database": "postgres",  # Default database
            "user": "postgres",
            "password": ""  # Try without password (peer auth)
        },
        {
            "host": "localhost",
            "port": "5432", 
            "database": "postgres",
            "user": "solifugus",  # Try with current user
            "password": ""
        },
        {
            "host": "/var/run/postgresql",  # Unix socket
            "port": "5432",
            "database": "postgres", 
            "user": "solifugus",
            "password": ""
        }
    ]
    
    for i, config in enumerate(configs_to_try, 1):
        print(f"\n{i}. Testing connection with user '{config['user']}'...")
        try:
            db = PostgreSQLDataLink(config, debug=False)
            
            if db.test_connection():
                print(f"✅ Success! Connected as {config['user']}")
                
                # Try to list databases
                try:
                    dbs = db.sql_get("SELECT datname FROM pg_database WHERE datistemplate = false")
                    print(f"   Found {len(dbs)} databases:")
                    for db_info in dbs[:3]:
                        print(f"   - {db_info['datname']}")
                    return True
                except Exception as e:
                    print(f"   Connected but query failed: {e}")
                
            else:
                print(f"❌ Connection failed")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}...")
    
    print("\n❌ All connection attempts failed")
    print("   Try running: sudo -u postgres createdb triai_main")
    print("   Or check PostgreSQL configuration")
    return False


if __name__ == "__main__":
    main()