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

### Quick Start

**New to the project?** See [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide!

### Prerequisites

- Docker and Docker Compose
- AWS account with S3 bucket
- OpenAI or Groq API key

### Detailed Setup

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

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

### Demo Walkthrough

To see the system in action with sample data, follow the [DEMO.md](DEMO.md) guide.

### Testing

Run the automated integration test suite:
```bash
./run_integration_tests.sh
```

For comprehensive testing documentation, see [TESTING.md](TESTING.md)

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

### Unit Testing

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

### Integration Testing

Run the full integration test suite:
```bash
./run_integration_tests.sh
```

See [TESTING.md](TESTING.md) for detailed testing procedures

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

## Documentation

📚 **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete guide to all documentation

### Quick Links

- **[QUICKSTART.md](QUICKSTART.md)** ⚡ - Get started in 5 minutes
- **[DEPLOYMENT.md](DEPLOYMENT.md)** 🚀 - Complete deployment guide
- **[DEMO.md](DEMO.md)** 🎬 - Step-by-step demo walkthrough
- **[TESTING.md](TESTING.md)** 🧪 - Integration testing guide
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** ✅ - Deployment verification
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)

## Sample Data

Sample documents for testing are available in the `sample_data/` directory:
- `data_privacy_policy.txt` - Sample policy document with compliance rules
- `violation_document.txt` - Sample document with multiple violations
- `compliant_document.txt` - Sample compliant document (no violations)

Convert these to PDF format for testing with the system.

## Architecture

The system follows a microservices-inspired architecture:

```
Frontend (React) → API (FastAPI) → PostgreSQL (metadata)
                                 → ChromaDB (vectors)
                                 → AWS S3 (documents)
                                 → OpenAI/Groq (LLM)
```

Key workflows:
1. **Policy Processing**: Upload → Parse → Chunk → Embed → Store
2. **Rule Extraction**: Retrieve chunks → LLM analysis → Store rules
3. **Document Audit**: Upload → Parse → Chunk → Embed → Compare → Detect violations
4. **Remediation**: Generate AI-powered suggestions for each violation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `./run_integration_tests.sh`
5. Submit a pull request

## License

MIT
