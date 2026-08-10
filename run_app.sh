#!/bin/bash

# ==============================================================================
# Agentic Debate Arena — One-Click Runner Script
# Launches both FastAPI Backend (port 8000) and React Frontend (port 5173).
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "======================================================================"
echo " ⚔️  Launching Agentic Debate Arena..."
echo "======================================================================"

# Ensure cleanup on exit / Ctrl+C
cleanup() {
  echo ""
  echo "🛑 Shutting down backend and frontend processes cleanly..."
  if [ -n "$BACKEND_PID" ]; then kill -TERM "$BACKEND_PID" 2>/dev/null; fi
  if [ -n "$FRONTEND_PID" ]; then kill -TERM "$FRONTEND_PID" 2>/dev/null; fi
  kill $(jobs -p) 2>/dev/null
  fuser -k -9 8000/tcp 5173/tcp >/dev/null 2>&1
  echo "✅ Stopped all servers."
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Free any stale processes on ports 8000 and 5173
fuser -k 8000/tcp 5173/tcp >/dev/null 2>&1

# 1. Start Backend FastAPI Server
echo "🚀 Starting FastAPI Backend on http://localhost:8000..."
cd "$BACKEND_DIR"
if [ -d "venv" ]; then
  source venv/bin/activate
fi

export PYTHONPATH="$BACKEND_DIR/app:$BACKEND_DIR:$PYTHONPATH"

# Use uvicorn --app-dir to set app directory as the import root
python -m uvicorn main:app --app-dir "$BACKEND_DIR/app" --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# 2. Start Frontend Vite Server
echo "⚡ Starting React Frontend on http://localhost:5173..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "======================================================================"
echo " ✅ Application is live!"
echo " 🌐 Frontend UI:  http://localhost:5173"
echo " ⚙️  Backend API: http://localhost:8000 (Docs: http://localhost:8000/docs)"
echo "======================================================================"
echo " Press Ctrl+C to stop both servers."
echo ""

# Keep script running to maintain background jobs
wait
