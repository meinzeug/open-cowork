#!/bin/bash

# Exit on error
set -e

echo "======================================================================"
echo "📦 Installation von Host-Abhängigkeiten (Ubuntu/Debian)"
echo "======================================================================"

# Update package index
sudo apt-get update

# Install Docker if not present
if ! [ -x "$(command -v docker)" ]; then
    echo "Docker wird installiert..."
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Add current user to docker group so sudo isn't needed
    sudo usermod -aG docker $USER
    echo "✓ Docker erfolgreich installiert. Du musst dich eventuell neu einloggen, damit die Docker-Gruppe aktiv wird."
else
    echo "✓ Docker ist bereits installiert."
fi

# Install Docker Compose if not present
if ! [ -x "$(command -v docker-compose)" ]; then
    echo "Docker Compose wird installiert..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose erfolgreich installiert."
else
    echo "✓ Docker Compose ist bereits installiert."
fi

echo "======================================================================"
echo "🎉 Alle systemweiten Host-Abhängigkeiten geprüft/installiert!"
echo "👉 Starte das System mit: ./start.sh"
echo "======================================================================"
