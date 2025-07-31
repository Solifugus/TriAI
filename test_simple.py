"""
Simple test to debug the mock data issue.
"""

from mock_datalink import MockDataLink

# Initialize mock DataLink
mock_instances = [{"instance": "mock\\server", "user": "mock_user", "password": "mock_pass"}]
db = MockDataLink(mock_instances, home_db="MockDB", debug=True)

print("Testing AI_Messages query:")
try:
    query = """
    SELECT Message_ID, Posted, User_From, User_To, Message, User_Read
    FROM AI_Messages 
    WHERE (User_From = 'DataAnalyst' AND User_To = 'testuser')
       OR (User_From = 'testuser' AND User_To = 'DataAnalyst')
    ORDER BY Posted DESC
    LIMIT 50
    """
    
    messages = db.sql_get(query)
    print(f"Found {len(messages)} messages")
    
    for msg in messages:
        print(f"Message: {msg}")
        print(f"Keys: {list(msg.keys())}")
        break
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()