#!/bin/bash

# TriAI Complete Setup Script
# Handles full installation, configuration, and deployment

set -e  # Exit on any error

echo "==============================================="
echo "TriAI Multi-Agent Framework Setup"
echo "==============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
INSTALL_DIR="/opt/triai"
SERVICE_USER="triai"
DB_SCHEMA_FILE="create_database_schema.sql"
BACKUP_DIR="/opt/triai-backup-$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Please do not run this script as root."
        log_info "This script will create a dedicated 'triai' user for security."
        exit 1
    fi
}

check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if we have sudo access
    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo access. Please ensure you can run sudo commands."
        exit 1
    fi
    
    # Check for required commands
    for cmd in python3 pip3 systemctl; do
        if ! command -v $cmd &> /dev/null; then
            log_error "Required command '$cmd' not found. Please install it first."
            exit 1
        fi
    done
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -ne 1 ]]; then
        log_error "Python 3.8+ is required. Found version: $PYTHON_VERSION"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

create_user() {
    log_step "Creating TriAI system user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        log_warn "User '$SERVICE_USER' already exists, skipping user creation"
    else
        sudo useradd -r -s /bin/bash -d $INSTALL_DIR -c "TriAI Service User" $SERVICE_USER
        log_info "Created system user '$SERVICE_USER'"
    fi
}

backup_existing() {
    if [[ -d "$INSTALL_DIR" ]]; then
        log_step "Backing up existing installation..."
        sudo cp -r "$INSTALL_DIR" "$BACKUP_DIR"
        log_info "Backup created at: $BACKUP_DIR"
    fi
}

install_application() {
    log_step "Installing TriAI application..."
    
    # Create installation directory
    sudo mkdir -p $INSTALL_DIR
    sudo chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    
    # Copy application files
    log_info "Copying application files..."
    sudo cp *.py $INSTALL_DIR/ 2>/dev/null || true
    sudo cp -r public $INSTALL_DIR/ 2>/dev/null || true
    sudo cp requirements.txt $INSTALL_DIR/ 2>/dev/null || true
    sudo cp *.sql $INSTALL_DIR/ 2>/dev/null || true
    
    # Set ownership
    sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    
    log_info "Application files installed"
}

setup_python_environment() {
    log_step "Setting up Python virtual environment..."
    
    cd $INSTALL_DIR
    
    # Create virtual environment as triai user
    sudo -u $SERVICE_USER python3 -m venv venv
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install -r requirements.txt
    
    log_info "Python environment ready"
}

configure_application() {
    log_step "Configuring TriAI application..."
    
    # Create config from template if it doesn't exist
    if [[ ! -f "$INSTALL_DIR/config.yaml" ]]; then
        if [[ -f "$INSTALL_DIR/config.yaml.template" ]]; then
            sudo cp "$INSTALL_DIR/config.yaml.template" "$INSTALL_DIR/config.yaml"
            sudo chown $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR/config.yaml"
            log_info "Created config.yaml from template"
        else
            log_warn "No config template found. You'll need to create config.yaml manually."
        fi
    else
        log_info "Configuration file already exists"
    fi
}

install_systemd_services() {
    log_step "Installing systemd services..."
    
    # Install service files
    if [[ -d "systemd" ]]; then
        sudo cp systemd/*.service /etc/systemd/system/
        sudo systemctl daemon-reload
        log_info "Systemd services installed"
    else
        log_warn "No systemd directory found, skipping service installation"
    fi
}

setup_database() {
    log_step "Database setup..."
    
    if [[ -f "$DB_SCHEMA_FILE" ]]; then
        log_info "Database schema file found: $DB_SCHEMA_FILE"
        log_warn "Please run this SQL script on your SQL Server database:"
        echo "  $INSTALL_DIR/$DB_SCHEMA_FILE"
    else
        log_warn "No database schema file found"
    fi
}

test_installation() {
    log_step "Testing installation..."
    
    cd $INSTALL_DIR
    
    # Test Python environment
    if sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python -c "import fastapi, uvicorn, websockets, yaml, pyodbc"; then
        log_info "Python dependencies test: PASSED"
    else
        log_error "Python dependencies test: FAILED"
        return 1
    fi
    
    # Test config file
    if [[ -f "$INSTALL_DIR/config.yaml" ]]; then
        log_info "Configuration file test: PASSED"
    else
        log_error "Configuration file test: FAILED"
        return 1
    fi
    
    # Test main application file
    if [[ -f "$INSTALL_DIR/main.py" ]]; then
        log_info "Main application test: PASSED"
    else
        log_error "Main application test: FAILED"
        return 1
    fi
    
    log_info "Installation tests completed successfully"
}

show_next_steps() {
    echo ""
    echo "==============================================="
    echo -e "${GREEN}TriAI Installation Complete!${NC}"
    echo "==============================================="
    echo ""
    echo "Next Steps:"
    echo ""
    echo "1. Configure Database Connection:"
    echo "   Edit: $INSTALL_DIR/config.yaml"
    echo "   Update your SQL Server settings (server, username, password, database)"
    echo ""
    echo "2. Setup Database Schema:"
    echo "   Run the SQL script on your SQL Server:"
    echo "   $INSTALL_DIR/$DB_SCHEMA_FILE"
    echo ""
    echo "3. Test the Installation:"
    echo "   cd $INSTALL_DIR"
    echo "   sudo -u $SERVICE_USER ./venv/bin/python main.py"
    echo ""
    echo "4. Enable Production Services:"
    echo "   sudo systemctl enable triai-messaging.service"
    echo "   sudo systemctl enable triai-agents.service"
    echo "   sudo systemctl start triai-messaging.service"
    echo "   sudo systemctl start triai-agents.service"
    echo ""
    echo "5. Check Service Status:"
    echo "   sudo systemctl status triai-messaging.service"
    echo "   sudo systemctl status triai-agents.service"
    echo ""
    echo "6. View Logs:"
    echo "   sudo journalctl -u triai-messaging.service -f"
    echo "   sudo journalctl -u triai-agents.service -f"
    echo ""
    echo "7. Access Web Interface:"
    echo "   http://your-server:8080"
    echo ""
    echo "==============================================="
    echo -e "${BLUE}Installation Directory:${NC} $INSTALL_DIR"
    echo -e "${BLUE}Service User:${NC} $SERVICE_USER"
    if [[ -d "$BACKUP_DIR" ]]; then
        echo -e "${BLUE}Backup Location:${NC} $BACKUP_DIR"
    fi
    echo "==============================================="
    echo ""
    echo -e "${GREEN}Your agents will now execute database queries directly!${NC}"
    echo -e "${GREEN}No more 'I can help you write a query' responses!${NC} 🎉"
    echo ""
}

# Main installation flow
main() {
    echo "Starting TriAI installation..."
    echo ""
    
    check_root
    check_prerequisites
    create_user
    backup_existing
    install_application
    setup_python_environment
    configure_application
    install_systemd_services
    setup_database
    test_installation
    
    show_next_steps
}

# Handle interruption
trap 'log_error "Installation interrupted by user"; exit 1' INT

# Run main installation
main "$@"