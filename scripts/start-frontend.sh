#!/bin/bash
# Start the frontend development server

set -e

cd "$(dirname "$0")/../client"

echo "🎨 Starting Frontend Server..."

# Install dependencies if needed
if [ ! -d node_modules ]; then
    echo "📦 Installing dependencies..."
    pnpm install
fi

# Start vite dev server
echo "✓ Starting server on http://localhost:5173"
echo ""

pnpm dev
