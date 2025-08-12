#!/bin/bash

# TriAI Deployment Package Creation Script
# Creates a production-ready package with MCP tools integration

echo "Creating TriAI Production Deployment Package..."
echo "================================================"

# Create deployment directory
DEPLOY_DIR="triai_deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

echo "Creating deployment directory: $DEPLOY_DIR"

# Copy core system files
echo "Copying core system files..."
cp main.py "$DEPLOY_DIR/"
cp enhanced_agent_server.py "$DEPLOY_DIR/"
cp mcp_tools_sqlserver.py "$DEPLOY_DIR/"
cp schema_compatibility.py "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"

# Copy database integration files
echo "Copying database integration files..."
cp datalink.py "$DEPLOY_DIR/"
cp mcp_tools.py "$DEPLOY_DIR/"
cp models.py "$DEPLOY_DIR/"

# Copy web client
echo "Copying web client..."
cp -r public "$DEPLOY_DIR/"

# Copy additional tools and compatibility files  
echo "Copying additional files..."
cp mcp_tools_pg.py "$DEPLOY_DIR/"  # For PostgreSQL support
cp mock_datalink.py "$DEPLOY_DIR/"  # For testing

# Create production config template
echo "Creating production configuration template..."
cat > "$DEPLOY_DIR/config.yaml.template" << 'EOF'
# TriAI Production Configuration Template
# Copy this to config.yaml and update with your settings

database:
  type: "sqlserver"  # Options: postgresql, sqlserver, mock
  
  # SQL Server configuration
  sqlserver:
    instances:
      - instance: "YOUR_SERVER\\YOUR_INSTANCE"  # Update with your SQL Server
        user: "YOUR_USERNAME"                   # Update with your username
        password: "YOUR_PASSWORD"               # Update with your password
    home_db: "TriAI_Main"                      # Update with your database name

server:
  host: "0.0.0.0"
  port: 8080
  public_folder: "./public" 
  reload: false
  use_mock_db: false  # IMPORTANT: Set to false for production

application:
  name: "TriAI"
  display_name: "TriAI Analytics Platform"
  description: "Multi-agent AI framework with database integration"

fastapi:
  title: "TriAI Messaging Server"
  description: "Multi-agent AI framework with MCP database integration"
  version: "1.0.0"
  docs_url: "/docs"
  redoc_url: "/redoc"

user:
  current_user: "admin"  # Update with your username

# Agent configuration - these should match your AI_Agents database table
agents:
  - name: "DataAnalyst"
    description: "Analyzes business data and generates reports"
    model_api: "ollama"
    model: "qwen2.5-coder"
    polling_interval: 3
    
  - name: "QueryBot"
    description: "Executes database queries and explains results"
    model_api: "ollama"
    model: "qwen2.5-coder"
    polling_interval: 3

# Ollama Configuration
ollama:
  base_url: "http://localhost:11434"  # Update if Ollama is on different server
  timeout: 60

# Agent Server Settings
agent_server:
  messaging_server_url: "ws://localhost:8080"  # Update if needed
  reconnect_attempts: 5
  reconnect_delay: 5
EOF

# Create database schema script
echo "Creating database schema script..."
cat > "$DEPLOY_DIR/create_database_schema.sql" << 'EOF'
-- TriAI Database Schema for SQL Server
-- Run this script on your SQL Server database

USE [TriAI_Main]  -- Change to your database name
GO

-- Agent registration and configuration
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Agents' AND xtype='U')
CREATE TABLE dbo.AI_Agents(
    Agent              VARCHAR(15) UNIQUE NOT NULL,
    Description        VARCHAR(100),       -- public description
    Role               VARCHAR(MAX),       -- agent's system prompt
    Model_API          VARCHAR(300),
    Model              VARCHAR(100),
    Polling_Interval   INT,
    PRIMARY KEY (Agent)
)
GO

-- Message storage between users and agents
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Messages' AND xtype='U')
CREATE TABLE dbo.AI_Messages(
    Message_ID     INT IDENTITY(1,1),
    Posted         DATETIME DEFAULT GETDATE(),
    User_From      VARCHAR(15),
    User_To        VARCHAR(15),
    Message        VARCHAR(MAX),
    User_Read      DATETIME,
    PRIMARY KEY (Message_ID)
)
GO

-- Agent memory system for persistent knowledge
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Memories' AND xtype='U')
CREATE TABLE dbo.AI_Memories(
    Memory_ID      INT IDENTITY(1,1),
    Agent          VARCHAR(15),
    First_Posted   DATETIME DEFAULT GETDATE(),
    Times_Recalled INT DEFAULT 0,
    Last_Recalled  DATETIME,
    Memory_label   VARCHAR(100),
    Memory         VARCHAR(MAX),
    Related_To     VARCHAR(100),
    Purge_After    DATETIME,
    PRIMARY KEY (Memory_ID)
)
GO

-- Script storage and metadata (optional)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Scripts' AND xtype='U')
CREATE TABLE dbo.AI_Scripts(
    Language       VARCHAR(15),
    Folder         VARCHAR(100),
    FileName       VARCHAR(100),
    Summary        VARCHAR(6000),
    Script         VARCHAR(MAX) NULL
)
GO

-- Insert default agents (update as needed)
IF NOT EXISTS (SELECT * FROM AI_Agents WHERE Agent = 'DataAnalyst')
INSERT INTO AI_Agents(Agent, Description, Role, Model_API, Model, Polling_Interval)
VALUES(
    'DataAnalyst',
    'Analyzes business data and generates reports',
    'You are a data analyst who proactively queries databases to answer user questions about business data, customer information, and analytics. When users ask about data, execute queries directly instead of offering to help them write queries.',
    'ollama',
    'qwen2.5-coder',
    3
)
GO

IF NOT EXISTS (SELECT * FROM AI_Agents WHERE Agent = 'QueryBot') 
INSERT INTO AI_Agents(Agent, Description, Role, Model_API, Model, Polling_Interval)
VALUES(
    'QueryBot',
    'Executes database queries and explains results',
    'You are a database query specialist who directly executes SQL queries to retrieve and analyze data for users. Always be proactive - if you can answer a question by querying data, DO IT immediately.',
    'ollama', 
    'qwen2.5-coder',
    3
)
GO

PRINT 'TriAI database schema created successfully!'
GO
EOF

# Create systemd service files
echo "Creating systemd service files..."
mkdir -p "$DEPLOY_DIR/systemd"

cat > "$DEPLOY_DIR/systemd/triai-messaging.service" << 'EOF'
[Unit]
Description=TriAI Messaging Server
After=network.target

[Service]
Type=simple
User=triai
Group=triai
WorkingDirectory=/opt/triai
ExecStart=/opt/triai/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/triai

[Install]
WantedBy=multi-user.target
EOF

cat > "$DEPLOY_DIR/systemd/triai-agents.service" << 'EOF'
[Unit]
Description=TriAI Enhanced Agents
After=network.target triai-messaging.service

[Service]
Type=simple
User=triai
Group=triai
WorkingDirectory=/opt/triai
ExecStart=/opt/triai/venv/bin/python enhanced_agent_server.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/triai

[Install]
WantedBy=multi-user.target
EOF

# Create deployment script
echo "Creating deployment script..."
cat > "$DEPLOY_DIR/deploy.sh" << 'EOF'
#!/bin/bash

# TriAI Production Deployment Script
echo "Deploying TriAI to Production..."
echo "================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "Please do not run as root. Create a dedicated user for TriAI."
   exit 1
fi

# Create application directory
sudo mkdir -p /opt/triai
sudo chown $USER:$USER /opt/triai

# Copy application files
echo "Copying application files..."
cp *.py /opt/triai/
cp -r public /opt/triai/
cp requirements.txt /opt/triai/

# Create configuration from template
if [ ! -f /opt/triai/config.yaml ]; then
    echo "Creating configuration file..."
    cp config.yaml.template /opt/triai/config.yaml
    echo "⚠️  IMPORTANT: Edit /opt/triai/config.yaml with your database settings!"
else
    echo "Configuration file already exists, skipping..."
fi

# Set up Python virtual environment
echo "Setting up Python environment..."
cd /opt/triai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install systemd services
echo "Installing systemd services..."
sudo cp systemd/triai-messaging.service /etc/systemd/system/
sudo cp systemd/triai-agents.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "Deployment completed!"
echo "===================="
echo ""
echo "Next steps:"
echo "1. Run the database schema script: create_database_schema.sql"
echo "2. Edit /opt/triai/config.yaml with your database settings"
echo "3. Test the deployment:"
echo "   cd /opt/triai && source venv/bin/activate && python main.py"
echo "4. If test works, enable services:"
echo "   sudo systemctl enable triai-messaging.service"
echo "   sudo systemctl enable triai-agents.service"  
echo "   sudo systemctl start triai-messaging.service"
echo "   sudo systemctl start triai-agents.service"
echo ""
echo "Access the web interface at: http://your-server:8080"
EOF

chmod +x "$DEPLOY_DIR/deploy.sh"

# Create README
echo "Creating README..."
cat > "$DEPLOY_DIR/README.md" << 'EOF'
# TriAI Production Deployment Package

This package contains the enhanced TriAI system with proper MCP tools integration.

## What's New

✅ **Agents now execute database queries directly** (no more "I can help you write a query")  
✅ **SQL Server MCP tools** for direct database access  
✅ **Intelligent query analysis** - natural language to SQL conversion  
✅ **Enhanced agent server** with proactive database operations  
✅ **Multi-database compatibility** (SQL Server, PostgreSQL, Mock)  

## Quick Start

1. **Run deployment script:**
   ```bash
   ./deploy.sh
   ```

2. **Set up database:**
   - Run `create_database_schema.sql` on your SQL Server
   - Edit `/opt/triai/config.yaml` with your database settings

3. **Test the system:**
   ```bash
   cd /opt/triai
   source venv/bin/activate
   python main.py
   ```

4. **Enable production services:**
   ```bash
   sudo systemctl enable triai-messaging.service triai-agents.service
   sudo systemctl start triai-messaging.service triai-agents.service
   ```

5. **Access web interface:**
   Open http://your-server:8080

## Key Files

- `enhanced_agent_server.py` - Enhanced agents with MCP database access
- `mcp_tools_sqlserver.py` - SQL Server-specific MCP tools
- `main.py` - Updated messaging server with multi-database support
- `config.yaml.template` - Production configuration template
- `create_database_schema.sql` - Database schema script

## Testing

Ask an agent: "How many records are in the Customer table?"

**Expected result:** Agent executes query and returns actual count
**Wrong result:** Agent offers to help write the query

For detailed instructions, see DEPLOYMENT_GUIDE.md
EOF

# Copy deployment guide
cp DEPLOYMENT_GUIDE.md "$DEPLOY_DIR/"

# Create archive
echo "Creating deployment archive..."
tar -czf "${DEPLOY_DIR}.tar.gz" "$DEPLOY_DIR"

echo ""
echo "✅ Deployment package created successfully!"
echo "================================================"
echo ""
echo "Package contents:"
echo "  📁 Directory: $DEPLOY_DIR/"
echo "  📦 Archive:    ${DEPLOY_DIR}.tar.gz"
echo ""
echo "Key features of this deployment:"
echo "  ✅ Enhanced agents that execute database queries directly"
echo "  ✅ SQL Server MCP tools integration"
echo "  ✅ Multi-database compatibility"
echo "  ✅ Proactive query execution (no more 'I can help you write a query')"
echo "  ✅ Intelligent natural language to SQL conversion"
echo "  ✅ Production systemd services"
echo "  ✅ Complete deployment automation"
echo ""
echo "Next steps:"
echo "  1. Copy ${DEPLOY_DIR}.tar.gz to your production server"
echo "  2. Extract and run ./deploy.sh"
echo "  3. Configure database settings in config.yaml"
echo "  4. Run the database schema script"
echo "  5. Start the services"
echo ""
echo "Your agents will now ACTUALLY execute database queries! 🎉"