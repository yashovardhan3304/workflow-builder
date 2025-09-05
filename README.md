# No-Code/Low-Code Workflow Application

A visual workflow builder that enables users to create intelligent workflows using drag-and-drop components for document processing, LLM interactions, and knowledge extraction.

## Features

- 🎯 **Visual Workflow Builder**: Drag-and-drop interface using React Flow
- 📚 **Document Processing**: PDF text extraction and embedding generation
- 🤖 **LLM Integration**: OpenAI GPT and Gemini support
- 🔍 **Web Search**: SerpAPI integration for real-time information
- 💾 **Vector Storage**: ChromaDB for semantic search
- 💬 **Chat Interface**: Interactive query system

## Tech Stack

- **Frontend**: React.js with TypeScript
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Vector Store**: ChromaDB
- **Workflow Engine**: React Flow
- **LLM**: OpenAI GPT, Gemini
- **Embeddings**: OpenAI Embeddings
- **Web Search**: SerpAPI

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- Docker (optional)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Database Setup
```bash
# Create PostgreSQL database
createdb workflow_app

# Run migrations
cd backend
alembic upgrade head
```

## Project Structure

```
worlflow/
├── backend/                 # FastAPI backend
├── frontend/               # React frontend
├── docker-compose.yml      # Docker setup
├── kubernetes/             # K8s manifests (optional)
└── README.md
```

## API Endpoints

- `POST /api/workflows` - Create workflow
- `POST /api/workflows/{id}/execute` - Execute workflow
- `POST /api/documents/upload` - Upload documents
- `POST /api/chat` - Chat interface
- `GET /api/workflows` - List workflows

## License

MIT


