# CI/CD Pipeline

This directory contains the GitHub Actions workflows for the AI Compliance Auditor project.

## Workflows

### CI Pipeline (`ci.yml`)

The main CI pipeline runs on pushes and pull requests to `main` and `develop` branches.

#### Jobs

1. **Backend Linting** - Runs `ruff` to check Python code quality
2. **Backend Tests** - Runs `pytest` with PostgreSQL test database
3. **Frontend Linting** - Runs `eslint` to check JavaScript/React code quality
4. **Frontend Tests** - Runs `vitest` for frontend unit tests
5. **Docker Build** - Builds Docker images for both backend and frontend (only on push to main/develop)

#### Docker Push (Optional)

The workflow includes a commented-out `docker-push` job that can be enabled to push images to GitHub Container Registry (ghcr.io). To enable:

1. Uncomment the `docker-push` job in `ci.yml`
2. Ensure your repository has the necessary permissions for GITHUB_TOKEN
3. Images will be tagged with both `latest` and the commit SHA

#### Environment Variables

The backend tests require the following environment variables (set in the workflow):
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `AWS_ACCESS_KEY_ID` - AWS access key (test value)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (test value)
- `AWS_S3_BUCKET` - S3 bucket name (test value)
- `OPENAI_API_KEY` - OpenAI API key (test value)
- `CHROMA_HOST` - ChromaDB host
- `CHROMA_PORT` - ChromaDB port

## Local Testing

### Backend

```bash
# Install ruff
pip install ruff

# Run linting
cd backend
ruff check .

# Run tests
pip install pytest pytest-asyncio pytest-cov httpx
pytest tests/ -v
```

### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Run linting
npm run lint

# Run tests
npm run test
```

### Docker Build

```bash
# Build backend
docker build -t ai-compliance-auditor-backend:local ./backend

# Build frontend
docker build -t ai-compliance-auditor-frontend:local ./frontend
```

## Configuration Files

- `backend/pyproject.toml` - Ruff and pytest configuration
- `frontend/vitest.config.js` - Vitest configuration
- `frontend/src/test/setup.js` - Test setup file
