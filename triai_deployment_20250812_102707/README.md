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
