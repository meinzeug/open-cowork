#!/bin/bash

set -euo pipefail

TARGET_USER="${SUDO_USER:-$USER}"

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
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add current user to docker group so sudo isn't needed
    sudo usermod -aG docker "$TARGET_USER"
    echo "✓ Docker erfolgreich installiert. Du musst dich eventuell neu einloggen, damit die Docker-Gruppe aktiv wird."
else
    echo "✓ Docker ist bereits installiert."
fi

# Install Docker Compose plugin if not present
if ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose Plugin wird installiert..."
    sudo apt-get update
    if sudo apt-get install -y docker-compose-plugin; then
        echo "✓ Docker Compose Plugin erfolgreich installiert."
    elif ! [ -x "$(command -v docker-compose)" ]; then
        echo "Fallback: standalone docker-compose wird installiert..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo "✓ Standalone Docker Compose erfolgreich installiert."
    fi
else
    echo "✓ Docker Compose Plugin ist bereits installiert."
fi

echo "Docker-Daemon wird aktiviert und gestartet..."
if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl enable --now docker
elif command -v service >/dev/null 2>&1; then
    sudo service docker start
else
    echo "⚠️  Kein systemctl/service gefunden. Starte den Docker-Daemon manuell, bevor du ./start.sh nutzt."
fi

if getent group docker >/dev/null 2>&1; then
    sudo usermod -aG docker "$TARGET_USER"
fi

echo "======================================================================"
echo "🎉 Alle systemweiten Host-Abhängigkeiten geprüft/installiert!"
echo "👉 Falls Docker ohne sudo noch nicht funktioniert: neu einloggen oder ausführen: newgrp docker"
echo "👉 Starte das System mit: ./start.sh"
echo "======================================================================"
