# AI Compliance Auditor - Deployment Guide

This guide provides step-by-step instructions for deploying the AI Compliance Auditor system using Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [AWS S3 Bucket Setup](#aws-s3-bucket-setup)
4. [Database Migration](#database-migration)
5. [Docker Compose Deployment](#docker-compose-deployment)
6. [Health Check Verification](#health-check-verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the AI Compliance Auditor, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **AWS Account** with S3 access
- **OpenAI API Key** or **Groq API Key** for LLM functionality
- **Git** (for cloning the repository)

Verify installations:
```bash
docker --version
docker-compose --version
```

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-compliance-auditor
```

### 2. Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with the following configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://compliance_user:compliance_pass@postgres:5432/compliance_db

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_S3_BUCKET=your-compliance-auditor-bucket
AWS_REGION=us-east-1

# LLM API Configuration (choose one or both)
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# JWT Authentication
JWT_SECRET=your_secure_random_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# ChromaDB Configuration
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Important Notes:**
- Replace all placeholder values with your actual credentials
- Generate a secure JWT secret: `openssl rand -hex 32`
- Never commit the `.env` file to version control

### 3. Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
cd ../frontend
cp .env.example .env
```

Edit `frontend/.env`:

```env
# API Configuration
VITE_API_URL=http://localhost:8000

# For production deployment, use your actual backend URL:
# VITE_API_URL=https://api.your-domain.com
```

## AWS S3 Bucket Setup

### 1. Create S3 Bucket

Using AWS Console:
1. Navigate to AWS S3 Console
2. Click "Create bucket"
3. Enter bucket name (e.g., `compliance-auditor-prod`)
4. Select region (e.g., `us-east-1`)
5. **Block Public Access**: Keep all public access blocked (recommended)
6. Enable versioning (optional but recommended)
7. Click "Create bucket"

Using AWS CLI:
```bash
aws s3 mb s3://your-compliance-auditor-bucket --region us-east-1
```

### 2. Configure Bucket Policy (Optional)

For enhanced security, create a bucket policy that restricts access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ComplianceAuditorAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_IAM_USER"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-compliance-auditor-bucket/*"
    }
  ]
}
```

### 3. Create IAM User (Recommended)

Create a dedicated IAM user for the application:

1. Navigate to IAM Console
2. Create new user: `compliance-auditor-app`
3. Attach policy: `AmazonS3FullAccess` or create custom policy with limited permissions
4. Generate access keys
5. Copy Access Key ID and Secret Access Key to `backend/.env`

Custom IAM Policy (least privilege):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-compliance-auditor-bucket",
        "arn:aws:s3:::your-compliance-auditor-bucket/*"
      ]
    }
  ]
}
```

### 4. Enable CORS (if needed for direct uploads)

If implementing direct browser uploads, configure CORS:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["http://localhost:3000", "https://your-domain.com"],
    "ExposeHeaders": ["ETag"]
  }
]
```

## Database Migration

The application uses Alembic for database migrations.

### 1. Initial Setup

Migrations are automatically applied when the backend container starts. However, you can run them manually if needed.

### 2. Manual Migration (if needed)

Access the backend container:
```bash
docker-compose exec backend bash
```

Run migrations:
```bash
alembic upgrade head
```

### 3. Verify Migrations

Check current migration version:
```bash
alembic current
```

View migration history:
```bash
alembic history
```

### 4. Migration Files

The following migrations are included:

1. **001_initial_organizations_users.py** - Creates organizations and users tables
2. **002_policies_and_chunks.py** - Creates policies and policy_chunks tables
3. **003_compliance_rules.py** - Creates compliance_rules table
4. **004_audit_documents_violations.py** - Creates audit_documents and violations tables

### 5. Rollback (if needed)

To rollback to a previous migration:
```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade <revision_id>  # Rollback to specific revision
```

## Docker Compose Deployment

### 1. Build and Start Services

From the project root directory:

```bash
docker-compose up --build -d
```

This command will:
- Build the backend Docker image
- Build the frontend Docker image
- Pull PostgreSQL and ChromaDB images
- Start all services in detached mode

### 2. Verify Services are Running

Check service status:
```bash
docker-compose ps
```

Expected output:
```
NAME                    STATUS              PORTS
backend                 Up                  0.0.0.0:8000->8000/tcp
frontend                Up                  0.0.0.0:3000->3000/tcp
postgres                Up                  5432/tcp
chromadb                Up                  0.0.0.0:8001->8000/tcp
```

### 3. View Logs

View all logs:
```bash
docker-compose logs -f
```

View specific service logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f chromadb
```

### 4. Stop Services

```bash
docker-compose down
```

To stop and remove volumes (WARNING: This deletes all data):
```bash
docker-compose down -v
```

### 5. Restart Services

```bash
docker-compose restart
```

Restart specific service:
```bash
docker-compose restart backend
```

## Health Check Verification

### 1. Backend Health Check

Check backend health:
```bash
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
  },
  "timestamp": "2025-02-12T10:30:00Z"
}
```

### 2. Frontend Access

Open browser and navigate to:
```
http://localhost:3000
```

You should see the login page.

### 3. API Documentation

Access interactive API documentation:
```
http://localhost:8000/docs
```

### 4. Database Connection Test

Test PostgreSQL connection:
```bash
docker-compose exec postgres psql -U compliance_user -d compliance_db -c "SELECT version();"
```

### 5. ChromaDB Test

Test ChromaDB connection:
```bash
curl http://localhost:8001/api/v1/heartbeat
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
```bash
# Find process using the port
lsof -i :8000
# Kill the process
kill -9 <PID>
# Or change port in docker-compose.yml
```

#### 2. Database Connection Failed

**Error**: `could not connect to server: Connection refused`

**Solution**:
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check DATABASE_URL in backend/.env
- Wait for PostgreSQL to fully start (may take 10-20 seconds)
- Check logs: `docker-compose logs postgres`

#### 3. S3 Access Denied

**Error**: `An error occurred (AccessDenied) when calling the PutObject operation`

**Solution**:
- Verify AWS credentials in backend/.env
- Check IAM user permissions
- Verify bucket name is correct
- Ensure bucket exists in the specified region

#### 4. ChromaDB Connection Failed

**Error**: `Could not connect to ChromaDB`

**Solution**:
- Ensure ChromaDB container is running
- Check CHROMA_HOST and CHROMA_PORT in backend/.env
- Restart ChromaDB: `docker-compose restart chromadb`

#### 5. Frontend Cannot Connect to Backend

**Error**: Network error or CORS issues

**Solution**:
- Verify VITE_API_URL in frontend/.env
- Check backend is running: `curl http://localhost:8000/health`
- Check CORS configuration in backend/app/main.py
- Clear browser cache and reload

#### 6. Migration Errors

**Error**: `alembic.util.exc.CommandError: Can't locate revision identified by`

**Solution**:
```bash
# Reset migrations (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d
```

#### 7. Out of Memory

**Error**: Container crashes or becomes unresponsive

**Solution**:
- Increase Docker memory allocation (Docker Desktop settings)
- Reduce batch sizes in embedding generation
- Monitor resource usage: `docker stats`

### Logs and Debugging

#### Enable Debug Logging

Edit `backend/.env`:
```env
LOG_LEVEL=DEBUG
```

Restart backend:
```bash
docker-compose restart backend
```

#### Access Container Shell

Backend:
```bash
docker-compose exec backend bash
```

Frontend:
```bash
docker-compose exec frontend sh
```

Database:
```bash
docker-compose exec postgres psql -U compliance_user -d compliance_db
```

#### Check Environment Variables

```bash
docker-compose exec backend env | grep -E "DATABASE_URL|AWS|OPENAI"
```

### Performance Optimization

#### 1. Database Indexing

Indexes are automatically created by migrations. Verify:
```sql
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';
```

#### 2. ChromaDB Performance

For large datasets, consider:
- Increasing ChromaDB memory allocation in docker-compose.yml
- Using persistent volumes for ChromaDB data

#### 3. Backend Workers

For production, consider using multiple workers:

Edit `backend/Dockerfile`:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Production Deployment Considerations

### 1. Security

- Use HTTPS with SSL certificates (Let's Encrypt)
- Enable firewall rules
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Implement rate limiting
- Enable audit logging

### 2. Scalability

- Use managed PostgreSQL (AWS RDS)
- Use managed S3 with CloudFront CDN
- Deploy backend with load balancer
- Use container orchestration (Kubernetes, ECS)

### 3. Monitoring

- Set up application monitoring (Datadog, New Relic)
- Configure log aggregation (ELK stack, CloudWatch)
- Set up alerts for errors and performance issues

### 4. Backup

- Enable automated PostgreSQL backups
- Enable S3 versioning and lifecycle policies
- Backup ChromaDB data regularly

### 5. CI/CD

- Use GitHub Actions for automated deployments
- Implement staging environment
- Run automated tests before deployment

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review health check: `curl http://localhost:8000/health`
- Consult API documentation: `http://localhost:8000/docs`

## Next Steps

After successful deployment:
1. Create your first organization and user account
2. Upload a sample policy document
3. Extract compliance rules
4. Upload a document for auditing
5. Review violations and remediation suggestions

See [DEMO.md](DEMO.md) for a complete walkthrough.
