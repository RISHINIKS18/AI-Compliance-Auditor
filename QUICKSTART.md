# AI Compliance Auditor - Quick Start Guide

Get up and running with the AI Compliance Auditor in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- AWS account with S3 bucket created
- OpenAI or Groq API key

## Step 1: Clone and Configure (2 minutes)

```bash
# Clone the repository
git clone <repository-url>
cd ai-compliance-auditor

# Set up backend environment
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your credentials:
```env
DATABASE_URL=postgresql://compliance_user:compliance_pass@postgres:5432/compliance_db
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
OPENAI_API_KEY=your_openai_key
JWT_SECRET=$(openssl rand -hex 32)
CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

```bash
# Set up frontend environment
cp frontend/.env.example frontend/.env
```

## Step 2: Start Services (1 minute)

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (30 seconds)
sleep 30

# Check health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "chromadb": "connected",
    "s3": "connected"
  }
}
```

## Step 3: Access the Application (30 seconds)

Open your browser:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Step 4: Try the Demo (2 minutes)

### Option A: Use the Web Interface

1. Register a new account at http://localhost:3000
2. Upload a policy document (use sample_data/data_privacy_policy.txt converted to PDF)
3. Wait for processing to complete
4. Extract compliance rules
5. Upload a document for audit (use sample_data/violation_document.txt converted to PDF)
6. View violations and remediation suggestions

### Option B: Use the API

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "DemoPass123!",
    "organization_name": "Demo Corp"
  }'

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "DemoPass123!"
  }' | jq -r '.access_token')

# Upload policy (if you have a PDF)
curl -X POST http://localhost:8000/api/policies/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_data/data_privacy_policy.pdf"
```

## Step 5: Run Tests (Optional)

```bash
# Run integration tests
./run_integration_tests.sh
```

## Troubleshooting

### Services not starting?
```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Can't connect to backend?
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check if port is in use
lsof -i :8000
```

### Database connection issues?
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

## Next Steps

- **Full Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup
- **Demo Walkthrough**: Follow [DEMO.md](DEMO.md) for complete feature tour
- **Testing Guide**: Review [TESTING.md](TESTING.md) for comprehensive testing

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U compliance_user -d compliance_db

# Run migrations
docker-compose exec backend alembic upgrade head
```

## Support

- Check health: `curl http://localhost:8000/health`
- View API docs: http://localhost:8000/docs
- Review logs: `docker-compose logs -f`

## What's Next?

1. Customize policies for your organization
2. Integrate with your document management system
3. Set up automated auditing workflows
4. Configure alerts for critical violations
5. Deploy to production (see DEPLOYMENT.md)

Happy auditing! 🚀
