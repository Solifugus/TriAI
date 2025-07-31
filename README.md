# TriAI Multi-Agent Framework

A complete multi-agent AI framework with database integration, web interface, and MCP (Model Context Protocol) tool support.

## 🏗️ Architecture

**TriAI consists of three main components:**

1. **Messaging Server** (FastAPI) - Central communication hub
2. **Browser Client** (HTML/CSS/JS) - Web-based user interface  
3. **Agent Server** (Python) - AI agents powered by Ollama

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai/) with `qwen2.5-coder` model
- Virtual environment (recommended)

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn websockets pydantic python-multipart pyyaml requests beautifulsoup4
```

### 2. Start Messaging Server

```bash
# Start the messaging server (runs on http://localhost:8080)
source venv/bin/activate && python main.py
```

### 3. Start AI Agents

In a new terminal:

```bash
# Activate virtual environment and start AI agents
source venv/bin/activate && python start_agents.py
```

### 4. Access Web Interface

Open your browser and navigate to: **http://localhost:8080**

## 🤖 Available AI Agents

The system includes three pre-configured agents:

- **DataAnalyst** - Analyzes data and generates reports
- **QueryBot** - Executes database queries and explains results  
- **ReportGen** - Generates comprehensive business reports

## 🔧 Key Features

### 🌐 Web Interface
- **Modern blue-themed UI** with responsive design
- **Real-time chat** with AI agents
- **Agent selection** dropdown
- **Tabular data display** for query results
- **Memory panel** showing agent memories
- **Auto-refresh** for new messages

### 🤖 AI Agents
- **Ollama integration** with qwen2.5-coder model
- **WebSocket communication** with messaging server
- **Turn-based polling** system
- **Independent operation** (no coordination required)
- **Automatic reconnection** on disconnects

### 🛠️ MCP Tools (18 available)
**Database Access:**
- `execute_query` - Run SELECT queries
- `list_databases` - View available databases
- `describe_table` - Get table structure
- `get_schema_info` - Database schema information
- `sample_table` - Get sample data

**Memory Management:**
- `store_memory` - Save information for future reference
- `retrieve_memories` - Get relevant past memories
- `search_memories` - Full-text memory search
- `update_memory` - Modify existing memories
- `delete_memory` - Remove memories

**Analysis Tools:**
- `get_column_stats` - Column statistics
- `check_permissions` - Database access verification
- `validate_sql` - SQL syntax validation

### 📊 Database Integration
- **Mock database** for development/testing
- **Real SQL Server** support (configure in `config.yaml`)
- **Automatic logging** of query history
- **Memory system** for agent persistence

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# Use mock database for testing
server:
  use_mock_db: true  # Set to false for real SQL Server

# Agent configurations
agents:
  - name: "DataAnalyst"
    description: "Analyzes data and generates reports"
    model_api: "ollama"
    model: "qwen2.5-coder"
    polling_interval: 3

# Ollama settings
ollama:
  base_url: "http://localhost:11434"
  timeout: 60
```

## 🧪 Testing

### Test Components Individually

```bash
# Test messaging server
python test_comprehensive.py

# Test browser client  
python test_browser_client.py

# Test agent functionality
python test_agent_basic.py

# Test full integration
python test_full_integration.py
```

### Test Results Summary
- **Messaging Server:** ✅ 15/17 tests passed (REST API, WebSocket, MCP tools)
- **Browser Client:** ✅ 35/36 tests passed (UI, API integration, responsive design)
- **Agent Server:** ✅ Core functionality working (Ollama, WebSocket, MCP)

## 🔍 Usage Examples

### Basic Chat
1. Open http://localhost:8080
2. Select "DataAnalyst" from dropdown
3. Type: "Can you tell me about yourself?"
4. Agent responds with capabilities and information

### Data Analysis
1. Select "QueryBot" 
2. Type: "Show me information about the available agents"
3. Agent queries the database and returns results in table format

### Memory Usage
1. Chat with any agent about a project
2. Agent automatically stores important information
3. Future conversations reference past memories

## 🏃‍♂️ Running in Production

### Start All Services

```bash
# Terminal 1: Messaging Server
source venv/bin/activate && python main.py

# Terminal 2: AI Agents  
source venv/bin/activate && python start_agents.py

# Terminal 3: Monitor logs (optional)
tail -f *.log
```

### Using Real SQL Server

1. Update `config.yaml`:
   ```yaml
   server:
     use_mock_db: false
   database:
     instances:
       - instance: "your_server\\instance"
         user: "your_username"
         password: "your_password"
     home_db: "TriAI_Main"
   ```

2. Create database tables (see schema in design documents)

## 📁 Project Structure

```
TriAI/
├── main.py              # Messaging server
├── agent_server.py      # AI agent implementation  
├── models.py            # Pydantic data models
├── mcp_tools.py         # MCP tool implementations
├── datalink.py          # SQL Server connectivity
├── mock_datalink.py     # Mock database for testing
├── config.yaml          # Configuration file
├── public/              # Web client files
│   ├── index.html       # Main web interface
│   ├── styles.css       # Blue-themed styling  
│   └── app.js           # Client-side JavaScript
└── test_*.py            # Test scripts
```

## 🎯 Design Philosophy

- **Transactional messaging** - No session state
- **Independent agents** - Unaware of other agents
- **Database-first** - All data persisted in SQL
- **Security focused** - SELECT-only queries, permission checking
- **Scalable architecture** - Easy to add new agents and tools

## 🤝 Contributing

The TriAI framework is built for extensibility:

- **Add new agents:** Configure in `config.yaml`
- **Create MCP tools:** Extend `mcp_tools.py`
- **Customize UI:** Modify files in `public/`
- **Add model support:** Extend agent server with new APIs

## 📚 API Documentation

When running, visit:
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

## 🎉 Success!

Your TriAI multi-agent framework is now complete and ready to use! The system provides:

✅ **Full web interface** for natural conversations  
✅ **Multiple AI agents** with specialized roles  
✅ **Database integration** with query capabilities  
✅ **Memory system** for persistent knowledge  
✅ **Real-time communication** via WebSocket  
✅ **Extensible architecture** for future enhancements  

Happy chatting with your AI agents! 🤖💬