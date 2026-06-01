#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_CMD=(docker)
COMPOSE_CMD=()

fail() {
    echo "❌ $1" >&2
    exit 1
}

detect_compose() {
    if "${DOCKER_CMD[@]}" compose version >/dev/null 2>&1; then
        COMPOSE_CMD=("${DOCKER_CMD[@]}" compose)
    elif command -v docker-compose >/dev/null 2>&1; then
        if [ "${DOCKER_CMD[0]}" = "sudo" ]; then
            COMPOSE_CMD=(sudo docker-compose)
        else
            COMPOSE_CMD=(docker-compose)
        fi
    else
        fail "Docker Compose fehlt. Führe zuerst ./install_ubuntu.sh aus."
    fi
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

ensure_docker_daemon() {
    if ! command -v docker >/dev/null 2>&1; then
        fail "Docker ist nicht installiert. Führe zuerst ./install_ubuntu.sh aus."
    fi

    if docker info >/dev/null 2>&1; then
        DOCKER_CMD=(docker)
        return
    fi

    if sudo docker info >/dev/null 2>&1; then
        echo "Docker läuft, aber dein Nutzer hat noch keinen direkten Zugriff. Starte vorerst mit sudo docker."
        echo "Für dauerhaften Zugriff später ausführen: newgrp docker"
        DOCKER_CMD=(sudo docker)
        return
    fi

    if ! docker_engine_present; then
        echo "Docker CLI gefunden, aber Docker Engine/service fehlt. Repariere Installation..."
        "$PROJECT_ROOT/install_ubuntu.sh"
    fi

    echo "Docker-Daemon ist nicht erreichbar. Versuche Docker zu starten..."
    if command -v systemctl >/dev/null 2>&1 && docker_service_exists; then
        sudo systemctl enable --now docker || true
        sleep 2
    elif command -v service >/dev/null 2>&1; then
        sudo service docker start || true
        sleep 2
    fi

    if docker info >/dev/null 2>&1; then
        DOCKER_CMD=(docker)
        return
    fi

    if sudo docker info >/dev/null 2>&1; then
        echo "Docker läuft, aber dein Nutzer hat noch keinen direkten Zugriff. Starte vorerst mit sudo docker."
        echo "Für dauerhaften Zugriff später ausführen: newgrp docker"
        DOCKER_CMD=(sudo docker)
        return
    fi

    echo "Docker ist weiterhin nicht erreichbar."
    echo
    echo "Prüfe diese Befehle auf dem Host:"
    echo "  sudo systemctl status docker --no-pager"
    echo "  sudo systemctl enable --now docker"
    echo
    if [ -S /var/run/docker.sock ] && ! groups "$USER" | grep -qw docker; then
        echo "Dein Nutzer ist vermutlich nicht in der docker-Gruppe:"
        echo "  sudo usermod -aG docker $USER"
        echo "  newgrp docker"
        echo "  ./start.sh"
    else
        echo "Wenn /var/run/docker.sock fehlt, läuft der Docker-Daemon nicht."
        echo "Installiere/repariere Docker mit:"
        echo "  ./install_ubuntu.sh"
    fi
    exit 1
}

echo "======================================================================"
echo "🚀 Bootstrapping Linux Cowork Agent (Open Cowork)..."
echo "======================================================================"

cd "$PROJECT_ROOT"

# 1. Ensure local workspace directory exists so Docker maps it as user-owned rather than root-owned
echo "Checking workspace folder..."
mkdir -p workspace

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env-Datei nicht gefunden! Kopiere .env.example..."
    cp .env.example .env
    echo "👉 Bitte editiere jetzt die '.env'-Datei und trage deine API-Keys ein."
fi

ensure_docker_daemon
detect_compose

# 3. Build and launch Docker Compose
echo "Starting Docker Compose services..."
"${COMPOSE_CMD[@]}" up --build
