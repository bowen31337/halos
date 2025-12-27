#!/bin/bash

# Claude.ai Clone - Development Environment Setup Script
# This script sets up the complete development environment for the Claude.ai clone
# with DeepAgents integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BACKEND_PORT=${BACKEND_PORT:-8000}
PROJECT_ROOT=$(cd "$(dirname "$0")" && pwd)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Claude.ai Clone - Environment Setup  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
            return 0
        fi
    fi
    return 1
}

# Function to check Node.js version
check_node_version() {
    if command_exists node; then
        NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
        if [ "$NODE_VERSION" -ge 20 ]; then
            return 0
        fi
    fi
    return 1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check for Python 3.11+
if check_python_version; then
    echo -e "${GREEN}✓ Python 3.11+ found${NC}"
else
    echo -e "${RED}✗ Python 3.11+ is required${NC}"
    echo "  Please install Python 3.11 or later"
    exit 1
fi

# Check for uv (Python package manager)
if command_exists uv; then
    echo -e "${GREEN}✓ uv package manager found${NC}"
else
    echo -e "${YELLOW}Installing uv package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check for Node.js 20+
if check_node_version; then
    echo -e "${GREEN}✓ Node.js 20+ found${NC}"
else
    echo -e "${RED}✗ Node.js 20+ is required${NC}"
    echo "  Please install Node.js 20 or later"
    exit 1
fi

# Check for pnpm
if command_exists pnpm; then
    echo -e "${GREEN}✓ pnpm found${NC}"
else
    echo -e "${YELLOW}Installing pnpm...${NC}"
    npm install -g pnpm
fi

echo ""
echo -e "${YELLOW}Setting up Python backend...${NC}"

cd "$PROJECT_ROOT"

# Create Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
uv pip install -r pyproject.toml 2>/dev/null || {
    # If pyproject.toml dependencies fail, install manually
    uv pip install \
        fastapi>=0.110.0 \
        uvicorn>=0.27.0 \
        sqlalchemy>=2.0.0 \
        pydantic>=2.0.0 \
        pydantic-settings>=2.0.0 \
        sse-starlette>=2.0.0 \
        python-multipart>=0.0.6 \
        aiofiles>=23.0.0 \
        python-jose>=3.3.0 \
        passlib>=1.7.4 \
        bcrypt>=4.0.0 \
        httpx>=0.25.0 \
        langchain-anthropic>=0.2.0 \
        langgraph>=0.2.0 \
        aiosqlite>=0.19.0 \
        deepagents>=0.3.1 \
        pytest>=8.0.0 \
        pytest-asyncio>=0.23.0 \
        pytest-cov>=4.0.0 \
        ruff>=0.2.0 \
        mypy>=1.8.0 \
        playwright>=1.40.0
}

# Install Playwright browsers if not installed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "Installing Playwright browsers..."
    .venv/bin/playwright install chromium
fi

echo -e "${GREEN}✓ Python backend setup complete${NC}"

echo ""
echo -e "${YELLOW}Setting up React frontend...${NC}"

cd "$PROJECT_ROOT/client"

# Check if client directory exists
if [ -d "$PROJECT_ROOT/client" ]; then
    # Install frontend dependencies
    if [ -f "package.json" ]; then
        echo "Installing frontend dependencies..."
        pnpm install
        echo -e "${GREEN}✓ Frontend setup complete${NC}"
    else
        echo -e "${YELLOW}! Frontend package.json not found, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}! Client directory not found, will be created later${NC}"
fi

cd "$PROJECT_ROOT"

# Setup environment variables
echo ""
echo -e "${YELLOW}Setting up environment...${NC}"

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=${BACKEND_PORT}
FRONTEND_PORT=${FRONTEND_PORT}

# Database
DATABASE_URL=sqlite:///./data/app.db

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Anthropic API (read from /tmp/api-key if available)
# ANTHROPIC_API_KEY=your-key-here

# DeepAgents Configuration
DEEPAGENTS_BACKEND=state
DEEPAGENTS_MEMORY_PATH=/memories/

# Feature Flags
EXTENDED_THINKING_ENABLED=true
MCP_ENABLED=true
PROMPT_CACHING_ENABLED=true
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create data directory
mkdir -p data logs reports/screenshots reports/test-results

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}       Environment Setup Complete       ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "To start the development servers, run:"
echo ""
echo -e "  ${GREEN}Backend:${NC}  cd $PROJECT_ROOT && source .venv/bin/activate && uvicorn src.main:app --reload --port $BACKEND_PORT"
echo -e "  ${GREEN}Frontend:${NC} cd $PROJECT_ROOT/client && pnpm dev"
echo ""
echo -e "Or use the convenience script:"
echo -e "  ${GREEN}./scripts/start-servers.sh${NC}"
echo ""
echo -e "Access the application:"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost:${FRONTEND_PORT}"
echo -e "  ${BLUE}Backend API:${NC}  http://localhost:${BACKEND_PORT}"
echo -e "  ${BLUE}API Docs:${NC}  http://localhost:${BACKEND_PORT}/docs"
echo -e "  ${BLUE}ReDoc:${NC}  http://localhost:${BACKEND_PORT}/redoc"
echo ""
echo -e "${YELLOW}Note:${NC} Set your Anthropic API key in .env or use /tmp/api-key"
echo ""
