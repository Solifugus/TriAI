#!/bin/bash

# TriAI Quick Setup - One-Command Installation
# This script creates the deployment package and installs TriAI

set -e

echo "=========================================="
echo "TriAI Quick Setup - One Command Install"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "main.py" ]] || [[ ! -f "enhanced_agent_server.py" ]]; then
    echo "❌ Error: Please run this script from the TriAI source directory"
    echo "   Required files not found: main.py, enhanced_agent_server.py"
    exit 1
fi

echo "✅ Found TriAI source files"

# Step 1: Create deployment package
echo ""
echo "📦 Step 1: Creating deployment package..."
if [[ -f "create_deployment_package.sh" ]]; then
    chmod +x create_deployment_package.sh
    ./create_deployment_package.sh
else
    echo "❌ Error: create_deployment_package.sh not found"
    exit 1
fi

# Find the latest deployment package
DEPLOY_PACKAGE=$(ls -t triai_deployment_*.tar.gz | head -n1)
if [[ -z "$DEPLOY_PACKAGE" ]]; then
    echo "❌ Error: No deployment package found"
    exit 1
fi

echo "✅ Created deployment package: $DEPLOY_PACKAGE"

# Step 2: Extract deployment package
echo ""
echo "📂 Step 2: Extracting deployment package..."
DEPLOY_DIR="${DEPLOY_PACKAGE%.tar.gz}"
tar -xzf "$DEPLOY_PACKAGE"
echo "✅ Extracted to: $DEPLOY_DIR"

# Step 3: Run installation
echo ""
echo "🚀 Step 3: Running installation..."
cd "$DEPLOY_DIR"

if [[ -f "install_triai.sh" ]]; then
    chmod +x install_triai.sh
    ./install_triai.sh
elif [[ -f "deploy.sh" ]]; then
    chmod +x deploy.sh
    ./deploy.sh
else
    echo "❌ Error: No installation script found in deployment package"
    exit 1
fi

echo ""
echo "🎉 TriAI Quick Setup Complete!"
echo ""
echo "The enhanced TriAI system is now installed and ready."
echo "Your agents will execute database queries directly instead of offering to help write them!"
echo ""