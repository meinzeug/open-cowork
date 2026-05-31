#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "======================================================================"
echo "🚀 Bootstrapping Linux Cowork Agent (Open Cowork)..."
echo "======================================================================"

# 1. Ensure local workspace directory exists so Docker maps it as user-owned rather than root-owned
echo "Checking workspace folder..."
mkdir -p workspace

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env-Datei nicht gefunden! Kopiere .env.example..."
    cp .env.example .env
    echo "👉 Bitte editiere jetzt die '.env'-Datei und trage deine API-Keys ein."
fi

# 3. Pull / Build and launch Docker Compose
echo "Starting Docker Compose services..."
docker-compose up --build
