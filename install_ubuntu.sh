#!/bin/bash

set -euo pipefail

TARGET_USER="${SUDO_USER:-$USER}"

echo "======================================================================"
echo "📦 Installation von Host-Abhängigkeiten (Ubuntu/Debian)"
echo "======================================================================"

install_base_packages() {
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
}

docker_service_exists() {
    if command -v systemctl >/dev/null 2>&1 \
        && systemctl list-unit-files docker.service --no-legend 2>/dev/null | grep -q "^docker.service"; then
        return 0
    fi

    [ -f /lib/systemd/system/docker.service ] || [ -f /usr/lib/systemd/system/docker.service ]
}

docker_engine_present() {
    command -v dockerd >/dev/null 2>&1 || docker_service_exists
}

docker_info() {
    docker info >/dev/null 2>&1
}

sudo_docker_info() {
    sudo docker info >/dev/null 2>&1
}

install_compose() {
    if docker compose version >/dev/null 2>&1; then
        echo "✓ Docker Compose Plugin ist bereits installiert."
        return
    fi

    echo "Docker Compose wird installiert..."
    sudo apt-get update
    if apt-cache show docker-compose-plugin >/dev/null 2>&1; then
        sudo apt-get install -y docker-compose-plugin
        echo "✓ Docker Compose Plugin erfolgreich installiert."
    elif apt-cache show docker-compose-v2 >/dev/null 2>&1; then
        sudo apt-get install -y docker-compose-v2
        echo "✓ Docker Compose v2 erfolgreich installiert."
    elif apt-cache show docker-compose >/dev/null 2>&1; then
        sudo apt-get install -y docker-compose
        echo "✓ Standalone Docker Compose aus Ubuntu erfolgreich installiert."
    else
        echo "Fallback: standalone docker-compose wird von GitHub installiert..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo "✓ Standalone Docker Compose erfolgreich installiert."
    fi
}

install_docker_from_official_repo() {
    echo "Versuche Installation/Reparatur über das offizielle Docker-Repository..."
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo rm -f /etc/apt/keyrings/docker.gpg
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    local codename
    codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
    if [ -z "$codename" ]; then
        codename="$(lsb_release -cs)"
    fi

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${codename} stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

    if ! sudo apt-get update; then
        echo "Offizielles Docker-Repository konnte nicht aktualisiert werden."
        return 1
    fi

    if ! apt-cache policy docker-ce | grep -Eq "Candidate: [0-9]"; then
        echo "Kein docker-ce Paket für Ubuntu-Codename '${codename}' gefunden."
        return 1
    fi

    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

install_docker_from_ubuntu_repo() {
    echo "Fallback: Installation/Reparatur über Ubuntu docker.io Pakete..."
    sudo rm -f /etc/apt/sources.list.d/docker.list
    sudo apt-get update
    sudo apt-get install -y docker.io
}

install_or_repair_docker_engine() {
    install_base_packages

    if docker_info || sudo_docker_info; then
        echo "✓ Docker Engine läuft bereits."
        return
    fi

    if command -v docker >/dev/null 2>&1 && docker_engine_present; then
        echo "✓ Docker Engine ist installiert, aber aktuell nicht erreichbar."
        return
    fi

    echo "Docker CLI ohne laufende Engine oder ohne docker.service erkannt. Engine wird installiert/repariert..."
    if install_docker_from_official_repo; then
        echo "✓ Docker Engine über offizielles Docker-Repository installiert."
    else
        install_docker_from_ubuntu_repo
        echo "✓ Docker Engine über Ubuntu-Repository installiert."
    fi
}

start_docker_daemon() {
    if docker_info || sudo_docker_info; then
        return
    fi

    echo "Docker-Daemon wird aktiviert und gestartet..."
    if command -v systemctl >/dev/null 2>&1 && docker_service_exists; then
        sudo systemctl daemon-reload
        sudo systemctl enable --now docker || true
    elif command -v service >/dev/null 2>&1; then
        sudo service docker start || true
    else
        echo "⚠️  Kein systemctl/service gefunden. Starte den Docker-Daemon manuell, bevor du ./start.sh nutzt."
    fi

    if docker_info || sudo_docker_info; then
        echo "✓ Docker-Daemon läuft."
        return
    fi

    echo "❌ Docker-Daemon ist weiterhin nicht erreichbar."
    echo "Prüfe:"
    echo "  sudo systemctl status docker --no-pager"
    echo "  sudo journalctl -u docker --no-pager -n 80"
    echo "  command -v dockerd"
    exit 1
}

ensure_docker_group() {
    if ! getent group docker >/dev/null 2>&1; then
        sudo groupadd docker || true
    fi
    sudo usermod -aG docker "$TARGET_USER"
}

install_or_repair_docker_engine
install_compose
start_docker_daemon
ensure_docker_group

echo "======================================================================"
echo "🎉 Alle systemweiten Host-Abhängigkeiten geprüft/installiert!"
echo "👉 Falls Docker ohne sudo noch nicht funktioniert: neu einloggen oder ausführen: newgrp docker"
echo "👉 Starte das System mit: ./start.sh"
echo "======================================================================"
