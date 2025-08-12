# TriAI Systemd Services

This directory contains systemd service files for managing the TriAI Multi-Agent Framework as system services.

## Service Files

- **`triai-messaging.service`** - Main messaging server (FastAPI)
- **`triai-agents.service`** - AI agent server
- **`triai.target`** - Target for managing both services together

## Installation

Run the installation script:
```bash
./install_services.sh
```

This will:
- Copy service files to `/etc/systemd/system/`
- Set proper permissions
- Enable the services
- Provide usage instructions

## Manual Installation

If you prefer manual installation:

```bash
# Copy service files
sudo cp triai-messaging.service /etc/systemd/system/
sudo cp triai-agents.service /etc/systemd/system/
sudo cp triai.target /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable triai-messaging.service
sudo systemctl enable triai-agents.service
sudo systemctl enable triai.target
```

## Usage

### Start/Stop All Services
```bash
sudo systemctl start triai.target      # Start all TriAI services
sudo systemctl stop triai.target       # Stop all TriAI services
sudo systemctl restart triai.target    # Restart all services
sudo systemctl status triai.target     # Check status
```

### Individual Service Management
```bash
# Messaging Server
sudo systemctl start triai-messaging.service
sudo systemctl stop triai-messaging.service
sudo systemctl status triai-messaging.service

# Agent Server
sudo systemctl start triai-agents.service
sudo systemctl stop triai-agents.service
sudo systemctl status triai-agents.service
```

### View Logs
```bash
# Follow all logs
sudo journalctl -u triai.target -f

# Follow messaging server logs
sudo journalctl -u triai-messaging.service -f

# Follow agent server logs
sudo journalctl -u triai-agents.service -f

# View recent logs
sudo journalctl -u triai-messaging.service --since "1 hour ago"
```

## Prerequisites

1. **Ollama Service** - Must be running for AI model access
   ```bash
   systemctl status ollama
   ```

2. **Virtual Environment** - Must be set up with dependencies
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Python Dependencies** - Install required packages
   ```bash
   pip install fastapi uvicorn websockets pydantic python-multipart pyyaml requests beautifulsoup4
   ```

## Service Configuration

### Messaging Server
- **Port**: 8080 (configurable in `config.yaml`)
- **Working Directory**: `/home/solifugus/development/TriAI`
- **Logs**: Available via `journalctl -u triai-messaging.service`

### Agent Server
- **Dependencies**: Requires messaging server to be running
- **Working Directory**: `/home/solifugus/development/TriAI`
- **Logs**: Available via `journalctl -u triai-agents.service`

## Troubleshooting

### Service Won't Start
1. Check service status: `sudo systemctl status triai-messaging.service`
2. View logs: `sudo journalctl -u triai-messaging.service -n 50`
3. Verify Ollama is running: `systemctl status ollama`
4. Check virtual environment exists and has dependencies

### Permission Issues
Ensure the service user (`solifugus`) has:
- Read access to the project directory
- Execute access to Python and virtual environment
- Write access for logs and temporary files

### Web Interface Not Accessible
1. Check if port 8080 is open: `sudo netstat -tlnp | grep 8080`
2. Verify firewall settings: `sudo ufw status`
3. Check service logs for binding errors

## Security Notes

The services are configured with security restrictions:
- `NoNewPrivileges=true` - Prevents privilege escalation
- `PrivateTmp=true` - Private temporary directory
- `ProtectSystem=strict` - Read-only system directories
- `ReadWritePaths=` - Specific writable paths only

## Auto-Start

Services are configured to start automatically on boot via `WantedBy=multi-user.target`.

To disable auto-start:
```bash
sudo systemctl disable triai.target
```

To re-enable:
```bash
sudo systemctl enable triai.target
```