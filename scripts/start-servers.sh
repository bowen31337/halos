#!/bin/bash

# Start both backend and frontend servers

set -e

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

echo "Starting Claude.ai Clone servers..."
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Error: Virtual environment not found. Run init.sh first."
    exit 1
fi

# Start backend server in background
echo "Starting backend server on port $BACKEND_PORT..."
cd "$PROJECT_ROOT"
source .venv/bin/activate
uvicorn src.main:app --reload --port $BACKEND_PORT &
BACKEND_PID=$!

# Start frontend server in background
if [ -d "$PROJECT_ROOT/client" ] && [ -f "$PROJECT_ROOT/client/package.json" ]; then
    echo "Starting frontend server on port $FRONTEND_PORT..."
    cd "$PROJECT_ROOT/client"
    pnpm dev --port $FRONTEND_PORT &
    FRONTEND_PID=$!
else
    echo "Warning: Frontend not found or not configured. Skipping..."
    FRONTEND_PID=""
fi

echo ""
echo "Servers started:"
echo "  Backend:  http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
echo "  API Docs: http://localhost:$BACKEND_PORT/docs"
if [ -n "$FRONTEND_PID" ]; then
    echo "  Frontend: http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)"
fi
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait
