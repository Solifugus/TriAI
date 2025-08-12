#!/bin/bash

# TriAI Production Setup from GitHub Clone
# Usage: git clone <repo> && cd TriAI && ./github_setup.sh

set -e

echo "==============================================="
echo "TriAI Production Setup from GitHub"
echo "==============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check we're in a TriAI repository
if [[ ! -f "main.py" ]] || [[ ! -f "enhanced_agent_server.py" ]]; then
    log_error "Not a TriAI repository. Run from TriAI directory after git clone."
    exit 1
fi

# Check not running as root
if [[ $EUID -eq 0 ]]; then
    log_error "Don't run as root. Script creates dedicated triai user."
    exit 1
fi

# Check sudo access
if ! sudo -n true 2>/dev/null; then
    log_error "Need sudo access. Run: sudo -v"
    exit 1
fi

log_info "Setting up TriAI from GitHub clone..."

# Create system user
if ! id "triai" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d /opt/triai -c "TriAI Service" triai
    log_info "Created triai user"
fi

# Install to /opt/triai
sudo mkdir -p /opt/triai
sudo cp -r * /opt/triai/
sudo chown -R triai:triai /opt/triai

# Create requirements.txt if missing
if [[ ! -f "/opt/triai/requirements.txt" ]]; then
    cat << 'EOF' | sudo tee /opt/triai/requirements.txt > /dev/null
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
websockets>=12.0
pyyaml>=6.0.1
requests>=2.31.0
pyodbc>=5.0.1
psycopg2-binary>=2.9.9
EOF
    sudo chown triai:triai /opt/triai/requirements.txt
fi

# Setup Python environment
cd /opt/triai
sudo -u triai python3 -m venv venv
sudo -u triai ./venv/bin/pip install -r requirements.txt

# Create config if missing
if [[ ! -f "/opt/triai/config.yaml" ]]; then
    cat << 'EOF' | sudo tee /opt/triai/config.yaml > /dev/null
database:
  type: "sqlserver"
  sqlserver:
    instances:
      - instance: "localhost\\SQLEXPRESS"
        user: "triai_user" 
        password: "your_password"
    home_db: "TriAI_Main"

server:
  host: "0.0.0.0"
  port: 8080
  use_mock_db: false

agents:
  - name: "DataAnalyst"
    description: "Analyzes business data"
    model_api: "ollama"
    model: "qwen2.5-coder"
  - name: "QueryBot"
    description: "Executes database queries"
    model_api: "ollama" 
    model: "qwen2.5-coder"

ollama:
  base_url: "http://localhost:11434"
EOF
    sudo chown triai:triai /opt/triai/config.yaml
fi

# Create systemd services
cat << 'EOF' | sudo tee /etc/systemd/system/triai-messaging.service > /dev/null
[Unit]
Description=TriAI Messaging Server
After=network.target

[Service]
Type=simple
User=triai
WorkingDirectory=/opt/triai
ExecStart=/opt/triai/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' | sudo tee /etc/systemd/system/triai-agents.service > /dev/null
[Unit]
Description=TriAI Agents
After=triai-messaging.service

[Service]
Type=simple
User=triai
WorkingDirectory=/opt/triai
ExecStart=/opt/triai/venv/bin/python enhanced_agent_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo ""
echo "==============================================="
echo -e "${GREEN}TriAI Setup Complete!${NC}"
echo "==============================================="
echo ""
echo "Next steps:"
echo "1. Edit database config: sudo nano /opt/triai/config.yaml"
echo "2. Test: cd /opt/triai && sudo -u triai ./venv/bin/python main.py"
echo "3. Enable services:"
echo "   sudo systemctl enable triai-messaging triai-agents"
echo "   sudo systemctl start triai-messaging triai-agents"
echo "4. Access: http://$(hostname):8080"
echo ""
echo "✅ Agents will now execute queries directly (no more 'help write' responses)!"