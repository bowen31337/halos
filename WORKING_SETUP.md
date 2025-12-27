# Working Development Setup

## Current Status: ✅ Backend Running

### Problem Identified
The project directory `/media/DATA/projects/autonomous-coding-clone-cc/talos` is on a mounted filesystem that **does not support memory-mapped shared objects** (`.so` and `.node` files).

### Solution Implemented
**Working directory in `/tmp`** with source code copied from the project.

### Working Configuration

#### Backend Server
- **Status**: ✅ Running
- **Port**: 8001 (8000 was occupied)
- **Working Directory**: `/tmp/talos-work`
- **Python Environment**: `/tmp/talos-work/backend-env`
- **Database**: `/tmp/talos-data/app.db`
- **Health Endpoint**: http://localhost:8001/health

#### Start Commands
```bash
# Backend (already running)
cd /tmp/talos-work
backend-env/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8001

# Logs location
tail -f /media/DATA/projects/autonomous-coding-clone-cc/talos/logs/backend.log
```

#### Project Files Location
- **Source Code**: `/media/DATA/projects/autonomous-coding-clone-cc/talos/src` → copied to `/tmp/talos-work/src`
- **Environment**: `/tmp/talos-work/.env`
- **Database**: `/tmp/talos-data/app.db`
- **Logs**: `/media/DATA/projects/autonomous-coding-clone-cc/talos/logs/backend.log`

### Installed Dependencies
```
fastapi==0.127.1
uvicorn==0.40.0
sqlalchemy==2.0.45
pydantic==2.12.5
pydantic-settings==2.12.0
sse-starlette==3.1.1
aiosqlite==0.19.0
langchain-anthropic==1.3.0
langgraph==1.0.5
deepagents==0.3.1
anthropic==0.75.0
```

### Frontend Status
❌ Not yet started - similar issue with vite native modules

### Next Steps
1. ✅ Backend running and healthy
2. ⏳ Start frontend (will need similar /tmp approach)
3. ⏳ Test basic chat functionality
4. ⏳ Implement features from feature_list.json

### API Endpoints Available
- `GET /health` - Health check ✅ Tested
- `GET /` - API info
- `GET /docs` - Swagger documentation
- `GET /api/conversations` - Conversation list
- `POST /api/agent/stream` - Agent streaming (not yet implemented)
- See `/docs` for full list

---
*Last Updated: Backend running successfully on port 8001*
*Date: 2025-12-27*
