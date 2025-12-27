# Claude.ai Clone - Advanced AI Chat Interface with Deep Agents

A fully functional clone of claude.ai, Anthropic's conversational AI interface, built with LangChain's DeepAgents framework for sophisticated agentic workflows.

## Features

### Core Chat
- Clean, centered chat layout with message bubbles
- Streaming message responses via LangGraph
- Markdown rendering with GitHub Flavored Markdown
- Code blocks with syntax highlighting and copy button
- LaTeX/math equation rendering with KaTeX
- Image upload, paste, and display
- Multi-turn conversations with full context

### Agentic Capabilities (via DeepAgents)
- **Task Planning**: Built-in `write_todos`/`read_todos` for structured task management
- **File Operations**: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`
- **Sub-Agent Delegation**: Specialized agents for research, code review, docs, tests
- **Context Management**: Auto-summarization at 170k tokens
- **Prompt Caching**: Anthropic prompt caching for cost reduction

### Extended Thinking
- Toggle extended thinking mode for complex problems
- Visible, collapsible thinking process
- Tool use during thinking
- Reasoning chain display

### Artifacts
- Code artifact viewer with syntax highlighting
- HTML/CSS/JS live preview
- React component preview with hot reload
- Mermaid diagram rendering
- Artifact versioning and history

### Human-in-the-Loop (HITL)
- Configurable permission modes (default, acceptEdits, plan, bypassPermissions)
- Approval dialogs for sensitive operations
- Audit trail for all decisions

### Additional Features
- Conversation management (create, rename, delete, archive, pin)
- Checkpoint system for safe rollbacks
- Projects with knowledge bases
- Long-term memory persistence
- Model selection (Claude Sonnet 4.5, Haiku 4.5, Opus 4.1)
- Custom instructions
- MCP server integration

## Tech Stack

### Frontend
- React 18+ with Vite 5
- Tailwind CSS 3.4+
- Zustand for state management
- React Router v6
- Monaco Editor for code editing
- Shiki for syntax highlighting
- KaTeX for math rendering
- Mermaid.js for diagrams

### Backend
- Python 3.11+ with FastAPI
- LangChain DeepAgents
- SQLAlchemy with SQLite
- Server-Sent Events (SSE) for streaming
- LangGraph for agent state management

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- uv (Python package manager)
- pnpm (Node.js package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd talos
```

2. Run the setup script:
```bash
chmod +x init.sh
./init.sh
```

3. Set your Anthropic API key:
```bash
# Option 1: In .env file
echo "ANTHROPIC_API_KEY=your-key-here" >> .env

# Option 2: Use /tmp/api-key
echo "your-key-here" > /tmp/api-key
```

4. Start the development servers:
```bash
# Terminal 1: Backend
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend
cd client
pnpm dev
```

### Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## Project Structure

```
talos/
├── src/                       # Backend source code
│   ├── api/                   # API routes/endpoints
│   │   └── routes/            # Route handlers
│   ├── models/                # SQLAlchemy database models
│   ├── services/              # Business logic layer
│   ├── schemas/               # Pydantic schemas
│   ├── utils/                 # Utility functions
│   ├── core/                  # Core config and database
│   └── main.py                # FastAPI application
│
├── client/                    # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── stores/            # Zustand stores
│   │   ├── pages/             # Page components
│   │   └── utils/             # Frontend utilities
│   └── public/                # Static assets
│
├── tests/                     # Test files
│   ├── e2e/                   # End-to-end tests
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
│
├── scripts/                   # Shell scripts
├── reports/                   # Generated reports
├── docs/                      # Documentation
└── logs/                      # Log files
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run E2E tests
pytest tests/e2e/

# Run specific test file
pytest tests/unit/test_conversations.py
```

## API Endpoints

### Conversations
- `GET /api/conversations` - List all conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/:id` - Get conversation details
- `DELETE /api/conversations/:id` - Delete conversation

### Agent
- `POST /api/agent/stream` - Stream agent response (SSE)
- `POST /api/agent/interrupt` - Handle HITL decisions
- `GET /api/agent/todos/:thread_id` - Get todo list

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `POST /api/projects/:id/files` - Upload file to project

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update settings

See `/docs` for complete API documentation.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_PORT` | Backend server port | 8000 |
| `FRONTEND_PORT` | Frontend dev server port | 5173 |
| `DATABASE_URL` | SQLite database path | sqlite:///./data/app.db |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `SECRET_KEY` | JWT secret key | (generated) |

### Permission Modes

| Mode | Description |
|------|-------------|
| `default` | Prompts for permission on each tool |
| `acceptEdits` | Auto-accepts file editing |
| `plan` | Read-only, no modifications |
| `bypassPermissions` | Full autonomy (trusted only) |

## Development

### Code Style
- Python: Ruff for linting, Black for formatting
- TypeScript: ESLint + Prettier
- Run `ruff check .` and `ruff format .`

### Type Checking
```bash
mypy src/
```

### Pre-commit
```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude API
- [LangChain](https://langchain.com/) for DeepAgents framework
- [claude.ai](https://claude.ai/) for UI/UX inspiration
