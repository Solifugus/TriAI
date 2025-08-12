# TriAI Installation Guide

## Quick Install from GitHub

### 1. Clone and Setup
```bash
git clone https://github.com/your-username/TriAI.git
cd TriAI
./github_setup.sh
```

### 2. Configure Database
```bash
sudo nano /opt/triai/config.yaml
```
Update your SQL Server settings:
- `instance`: Your SQL Server instance name
- `user`: Database username  
- `password`: Database password
- `home_db`: Database name

### 3. Setup Database Schema
Run this SQL script on your SQL Server:
```sql
-- See create_database_schema.sql in the repository
```

### 4. Test Installation
```bash
cd /opt/triai
sudo -u triai ./venv/bin/python main.py
```
Press Ctrl+C to stop the test.

### 5. Start Production Services
```bash
sudo systemctl enable triai-messaging triai-agents
sudo systemctl start triai-messaging triai-agents
```

### 6. Access Web Interface
Open: `http://your-server:8080`

## Key Feature

✅ **Agents execute database queries directly**  
❌ No more "I can help you write a query" responses  
🎯 Proactive data analysis with MCP tools

## Troubleshooting

Check service status:
```bash
sudo systemctl status triai-messaging triai-agents
```

View logs:
```bash
sudo journalctl -u triai-messaging -f
sudo journalctl -u triai-agents -f
```

## Requirements

- Ubuntu/Debian or RHEL/CentOS
- Python 3.8+
- SQL Server database
- Ollama (for AI models)

## Architecture

- **Messaging Server**: FastAPI + WebSocket communication
- **Enhanced Agents**: Proactive database querying with MCP tools  
- **Web Client**: Browser-based interface
- **Database**: SQL Server with TriAI schema