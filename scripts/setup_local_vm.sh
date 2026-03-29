#!/bin/bash
# ============================================================
# VCC Assignment 3 - Local VM Setup Script
# Sets up the local VM with all dependencies for monitoring
# and the sample Flask application.
# ============================================================

set -e

echo "=========================================="
echo " VCC Assignment 3 - Local VM Setup"
echo "=========================================="

# Update system packages
echo "[1/6] Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

# Install Python3 and pip
echo "[2/6] Installing Python3 and pip..."
sudo apt-get install -y python3 python3-pip python3-venv curl wget git

# Create virtual environment
echo "[3/6] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "[4/6] Installing Python dependencies..."
pip install -r requirements.txt

# Install Google Cloud SDK (if not already installed)
echo "[5/6] Checking Google Cloud SDK..."
if ! command -v gcloud &> /dev/null; then
    echo "Installing Google Cloud SDK..."
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
    tar -xf google-cloud-cli-linux-x86_64.tar.gz
    ./google-cloud-sdk/install.sh --quiet
    source ~/google-cloud-sdk/path.bash.inc
    echo "Run 'gcloud init' to configure your GCP project"
else
    echo "Google Cloud SDK already installed"
fi

# Load environment configuration
echo "[6/6] Loading configuration..."
if [ -f config/gcp_config.env ]; then
    export $(grep -v '^#' config/gcp_config.env | xargs)
    echo "Configuration loaded from config/gcp_config.env"
else
    echo "WARNING: config/gcp_config.env not found. Create it from the template."
fi

echo ""
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Update config/gcp_config.env with your GCP project details"
echo "  2. Run 'gcloud auth login' to authenticate"
echo "  3. Run 'gcloud config set project YOUR_PROJECT_ID'"
echo "  4. Start the app:     python src/app.py"
echo "  5. Start monitoring:  python src/monitor.py"
echo ""
