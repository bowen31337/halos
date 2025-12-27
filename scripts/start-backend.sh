#!/bin/bash
# Start the backend server

set -e

cd "$(dirname "$0")/.."

echo "🚀 Starting Backend Server..."

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start uvicorn
echo "✓ Starting server on http://localhost:8000"
echo "✓ API docs available at http://localhost:8000/docs"
echo ""

python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
