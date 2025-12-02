# AI Compliance Auditor

An MVP system designed to help organizations automatically detect compliance violations by ingesting company policies and documents, analyzing them using AI/LLM technology, and providing actionable remediation suggestions.

## Features

- Multi-tenant organization management
- Policy document upload and analysis
- Automated compliance rule extraction
- Document auditing against policies
- AI-powered violation detection
- Remediation suggestions
- Export audit reports (PDF/CSV)

## Tech Stack

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL (relational data)
- ChromaDB (vector storage)
- AWS S3 (document storage)
- OpenAI/Groq (LLM APIs)

### Frontend
- React 18
- Vite
- Tailwind CSS
- React Query
- React Router

## Getting Started

### Prerequisites

- Docker and Docker Compose
- AWS account with S3 bucket
- OpenAI or Groq API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-compliance-auditor
```

2. Set up environment variables:

Backend:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
```

Frontend:
```bash
cp frontend/.env.example frontend/.env
# Edit frontend/.env if needed
```

3. Start the services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Development

#### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Testing

Backend tests:
```bash
cd backend
pytest
```

Frontend tests:
```bash
cd frontend
npm test
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
├── .gitignore
└── README.md
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## License

MIT
