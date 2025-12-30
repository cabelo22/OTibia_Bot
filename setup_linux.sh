#!/bin/bash
# Setup script for Linux (Ubuntu/Debian)

set -e

echo "======================================"
echo "  OTibia Bot - Linux Setup Script"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}Error: This script is for Linux only${NC}"
    exit 1
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. Consider running as normal user.${NC}"
fi

echo "Step 1: Installing system dependencies..."
echo "This may require sudo password."
echo ""

sudo apt update

sudo apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    tesseract-ocr \
    tesseract-ocr-por \
    python3-pyqt5 \
    xdotool \
    build-essential \
    libx11-dev \
    libxtst-dev

echo -e "${GREEN}✓ System dependencies installed${NC}"
echo ""

echo "Step 2: Installing Python packages..."
pip3 install -r requirements.txt --user

echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

echo "Step 3: Configuring permissions..."
echo ""

# Configure ptrace
current_ptrace=$(cat /proc/sys/kernel/yama/ptrace_scope)
if [ "$current_ptrace" != "0" ]; then
    echo "Configuring ptrace permissions (required for memory reading)..."
    echo "This requires sudo access."
    
    read -p "Allow ptrace for same-user processes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
        
        # Make permanent
        if ! grep -q "kernel.yama.ptrace_scope" /etc/sysctl.conf; then
            echo "kernel.yama.ptrace_scope = 0" | sudo tee -a /etc/sysctl.conf
        fi
        echo -e "${GREEN}✓ Ptrace configured${NC}"
    else
        echo -e "${YELLOW}⚠ Ptrace not configured. You'll need to run the bot as root or configure manually.${NC}"
    fi
else
    echo -e "${GREEN}✓ Ptrace already configured${NC}"
fi

echo ""

# X11 permissions
echo "Configuring X11 permissions..."
xhost +local: 2>/dev/null || echo -e "${YELLOW}⚠ Could not configure X11. Run 'xhost +local:' manually if needed.${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "======================================"
echo ""
echo "To run the bot:"
echo "  python3 StartBot.py"
echo ""
echo "For troubleshooting, see INSTALL_LINUX.md"
echo ""
