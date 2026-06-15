#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define paths
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$BASE_DIR/backend"
FRONTEND_DIR="$BASE_DIR/frontend"

echo "=========================================================="
echo "      VirtualRadio - Iniciar Prototipo Técnico"
echo "=========================================================="

# 1. Setup Backend Python Virtual Environment
echo "📦 Configurando entorno virtual de Python..."
if [ ! -d "$BACKEND_DIR/venv" ]; then
    python3 -m venv "$BACKEND_DIR/venv"
fi

# Activate virtual environment
source "$BACKEND_DIR/venv/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📥 Instalando dependencias de Python (Flask, pydub, gTTS...)..."
pip install -r "$BACKEND_DIR/requirements.txt"

# 2. Install Frontend Node.js Dependencies
echo "📥 Instalando dependencias de Nuxt (Node.js)..."
cd "$FRONTEND_DIR"
npm install
cd "$BASE_DIR"

# 3. Launch Services
echo "🚀 Arrancando servicios..."

# Trap CTRL+C (SIGINT) and SIGTERM to kill background processes
cleanup() {
    echo ""
    echo "🛑 Deteniendo servicios de VirtualRadio..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    echo "👋 ¡Servicios detenidos!"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Run Flask Backend
echo "📡 Arrancando Flask API Backend en http://localhost:5000..."
source "$BACKEND_DIR/venv/bin/activate"
python3 "$BACKEND_DIR/app.py" > "$BACKEND_DIR/flask.log" 2>&1 &
BACKEND_PID=$!

# Give Flask a second to start
sleep 2

# Check if Flask is running
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "❌ Error: El backend de Flask no pudo iniciarse. Logs en backend/flask.log:"
    cat "$BACKEND_DIR/flask.log"
    exit 1
fi

# Run Nuxt Frontend
echo "💻 Arrancando Nuxt Frontend en http://localhost:3000..."
cd "$FRONTEND_DIR"
npm run dev -- --port 3000 > "$FRONTEND_DIR/nuxt.log" 2>&1 &
FRONTEND_PID=$!
cd "$BASE_DIR"

echo "=========================================================="
echo "🎉 ¡VirtualRadio está en línea!"
echo "   -> Frontend: http://localhost:3000"
echo "   -> Backend API: http://localhost:5000"
echo "=========================================================="
echo "Presiona [CTRL+C] para detener todos los servidores."
echo ""

# Keep script running to monitor background processes
wait
