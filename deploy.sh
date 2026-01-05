#!/bin/bash

# Configuration
SERVER_IP="45.147.7.54"
REMOTE_USER="root"
REMOTE_DIR="/root/Resell_Bot"

echo "🚀 Starting Deployment to $SERVER_IP..."

# 1. Check if auth.json exists locally
if [ ! -f "auth.json" ]; then
    echo "❌ Error: auth.json not found in current directory!"
    exit 1
fi

# 2. Check if .env exists locally
if [ ! -f ".env" ]; then
    echo "❌ Error: .env not found in current directory!"
    exit 1
fi

echo "🔹 Connecting to server to prepare environment..."
echo "⚠️  You will be asked for the server password (3VE2tsb7y1kt) multiple times unless you have SSH keys set up."

# 3. Setup Remote Server (Install Docker & Git)
ssh $REMOTE_USER@$SERVER_IP << 'ENDSSH'
    set -e
    echo "📦 Updating remote server..."
    apt-get update > /dev/null
    
    echo "📦 Installing Git & Docker..."
    if ! command -v docker &> /dev/null; then
        apt-get install -y git docker.io
        systemctl enable --now docker
    else
        echo "✅ Docker already installed."
    fi

    if ! command -v git &> /dev/null; then
        apt-get install -y git
    else
        echo "✅ Git already installed."
    fi
ENDSSH

# 4. Deployment Logic
echo "🔹 Deploying Code..."
ssh $REMOTE_USER@$SERVER_IP << EOF
    set -e
    if [ -d "$REMOTE_DIR" ]; then
        echo "🔄 Updating existing repo..."
        cd $REMOTE_DIR
        git pull origin main
    else
        echo "⬇️ Cloning repo..."
        git clone https://github.com/Nercc000/Resell_Bot.git $REMOTE_DIR
    fi
EOF

# 5. Transfer Secrets (auth.json, .env)
echo "🔹 Transferring secrets (auth.json, .env)..."
scp auth.json $REMOTE_USER@$SERVER_IP:$REMOTE_DIR/auth.json
scp .env $REMOTE_USER@$SERVER_IP:$REMOTE_DIR/.env
# Optional: device.json if it exists
if [ -f "device.json" ]; then
    scp device.json $REMOTE_USER@$SERVER_IP:$REMOTE_DIR/device.json
fi

# 6. Build and Restart Docker Compose
echo "🔹 Building and Restarting Docker Compose..."
ssh $REMOTE_USER@$SERVER_IP << 'ENDSSH'
    set -e
    cd /root/Resell_Bot
    
    # Stop old container if it exists (cleanup migration)
    docker stop ps5-bot 2>/dev/null || true
    docker rm ps5-bot 2>/dev/null || true
    
    echo "🧹 Freeing port 80..."
    fuser -k 80/tcp > /dev/null 2>&1 || true
    systemctl stop apache2 > /dev/null 2>&1 || true
    systemctl stop nginx > /dev/null 2>&1 || true

    echo "🐳 Starting Services (Backend + Caddy)..."
    # -v removes volumes (wipes old/broken SSL certs) to force fresh start
    docker compose down -v || true
    docker compose up -d --build
    
    echo "✅ Deployment SUCCESS!"
    echo "🌐 API is reachable via HTTPS: https://45.147.7.54.nip.io"
ENDSSH
