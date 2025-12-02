# Design Document

## Overview

The AI Compliance Auditor is a full-stack web application that leverages Large Language Models (LLMs) and vector embeddings to automatically detect compliance violations in organizational documents. The system follows a microservices-inspired architecture with a FastAPI backend, React frontend, PostgreSQL for relational data, ChromaDB for vector storage, and AWS S3 for document storage.

The core workflow involves: (1) ingesting policy documents, (2) parsing and chunking them, (3) generating embeddings, (4) extracting compliance rules using LLMs, (5) auditing uploaded documents against these rules, and (6) presenting violations with AI-generated remediation suggestions in a dashboard.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React + Vite UI]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend]
        Auth[JWT Auth Middleware]
    end
    
    subgraph "Processing Layer"
        Parser[Document Parser]
        Chunker[Text Chunker]
        Embedder[Embedding Generator]
        Classifier[Rule Classifier]
        Auditor[Compliance Auditor]
    end
    
    subgraph "Storage Layer"
        PG[(PostgreSQL)]
        S3[AWS S3]
        Chroma[(ChromaDB)]
    end
    
    subgraph "External Services"
        LLM[OpenAI/Groq API]
    end
    
    UI -->|HTTP/REST| API
    API --> Auth
    Auth --> Parser
    Auth --> Auditor
    Parser --> S3
    Parser --> Chunker
    Chunker --> PG
    Chunker --> Embedder
    Embedder --> Chroma
    Embedder --> LLM
    Classifier --> LLM
    Classifier --> Chroma
    Auditor --> Classifier
    Auditor --> PG
```

### Technology Stack Rationale

- **FastAPI**: High-performance async Python framework with automatic OpenAPI documentation
- **PostgreSQL**: Robust relational database for structured data (users, organizations, policies, violations)
- **ChromaDB**: Purpose-built vector database for embedding storage and similarity search
- **AWS S3**: Scalable object storage for PDF documents
- **React + Vite**: Modern frontend with fast HMR and optimized builds
- **Tailwind CSS + ShadCN**: Utility-first styling with accessible component library
- **NumPy**: Efficient numerical operations for token counting and vector manipulation
- **Pandas**: Data manipulation for report generation and CSV exports

### Multi-Tenant Architecture

The system implements row-level multi-tenancy:
- Every database table includes an `organization_id` foreign key
- API middleware extracts organization context from JWT tokens
- Database queries automatically filter by organization_id
- ChromaDB collections are namespaced by organization (e.g., `org_{org_id}_policies`)
- S3 paths follow pattern: `{org_id}/policies/{file_id}.pdf`

## Components and Interfaces

### Backend Components

#### 1. Authentication Module (`app/auth/`)

**Purpose**: Handle user authentication and JWT token management

**Key Classes**:
- `User` (SQLAlchemy model): id, email, hashed_password, organization_id, created_at
- `Organization` (SQLAlchemy model): id, name, created_at
- `AuthService`: Methods for registration, login, token generation/validation

**API Endpoints**:
```python
POST /api/auth/register
POST /api/auth/login
GET /api/auth/me
```

**Dependencies**: JWT library (python-jose), password hashing (passlib with bcrypt)

#### 2. Policy Management Module (`app/policies/`)

**Purpose**: Handle policy document upload, storage, and metadata management

**Key Classes**:
- `Policy` (SQLAlchemy model): id, organization_id, filename, s3_path, upload_date, status, file_size
- `PolicyChunk` (SQLAlchemy model): id, policy_id, chunk_index, content, token_count
- `PolicyService`: Methods for upload, retrieval, deletion

**API Endpoints**:
```python
POST /api/policies/upload
GET /api/policies
GET /api/policies/{policy_id}
DELETE /api/policies/{policy_id}
```

**S3 Integration**: Uses boto3 client with presigned URLs for secure uploads

#### 3. Document Processing Module (`app/processing/`)

**Purpose**: Parse PDFs, chunk text, and prepare for embedding

**Key Classes**:
- `DocumentParser`: Extract text from PDFs using PyMuPDF (fitz)
- `TextChunker`: Split text into ~500 token chunks with overlap
- `TokenCounter`: Use tiktoken or simple whitespace-based counting with NumPy

**Processing Pipeline**:
```python
1. Parse PDF → raw_text
2. Clean text (remove extra whitespace, normalize)
3. Chunk with 500-token windows and 50-token overlap
4. Store chunks in PostgreSQL
5. Trigger embedding generation
```

**Error Handling**: Catch parsing errors, log failures, mark policy status as "failed"

#### 4. Embedding Module (`app/embeddings/`)

**Purpose**: Generate and store vector embeddings for semantic search

**Key Classes**:
- `EmbeddingService`: Interface with OpenAI/Groq embedding APIs
- `VectorStore`: ChromaDB client wrapper for CRUD operations

**Embedding Pipeline**:
```python
1. Batch chunks (e.g., 100 at a time)
2. Call embedding API (OpenAI text-embedding-3-small or Groq)
3. Store vectors in ChromaDB with metadata (chunk_id, policy_id, org_id)
4. Use NumPy for cosine similarity verification
```

**ChromaDB Schema**:
- Collection per organization: `org_{org_id}_policies`
- Metadata: `{chunk_id, policy_id, chunk_index, content_preview}`

**API Endpoints**:
```python
POST /api/embeddings/generate/{policy_id}
POST /api/embeddings/search
```

#### 5. Rule Classification Module (`app/rules/`)

**Purpose**: Extract compliance rules from policy documents using LLMs

**Key Classes**:
- `ComplianceRule` (SQLAlchemy model): id, organization_id, policy_id, rule_text, category, severity, source_chunk_id
- `RuleClassifier`: LLM-based rule extraction service

**LLM Prompt Template**:
```
You are a compliance expert. Extract specific, actionable compliance rules from the following policy text.

Policy Text:
{policy_chunk}

For each rule, provide:
1. Rule description (clear, specific requirement)
2. Category (e.g., data privacy, financial, HR, security)
3. Severity (low, medium, high, critical)

Return as JSON array:
[
  {
    "rule_text": "...",
    "category": "...",
    "severity": "..."
  }
]
```

**Classification Pipeline**:
```python
1. Retrieve policy chunks from PostgreSQL
2. For each chunk, query ChromaDB for similar policy context
3. Build LLM prompt with chunk + context
4. Parse JSON response
5. Store rules in PostgreSQL
```

**API Endpoints**:
```python
POST /api/rules/extract/{policy_id}
GET /api/rules
GET /api/rules/{rule_id}
```

#### 6. Audit Module (`app/audits/`)

**Purpose**: Audit documents against compliance rules and detect violations

**Key Classes**:
- `AuditDocument` (SQLAlchemy model): id, organization_id, filename, s3_path, upload_date, status
- `Violation` (SQLAlchemy model): id, audit_document_id, rule_id, chunk_id, severity, detected_at, remediation
- `AuditService`: Orchestrate document auditing

**Audit Pipeline**:
```python
1. Upload document → S3
2. Parse and chunk document
3. Generate embeddings for chunks
4. For each chunk:
   a. Query ChromaDB for similar policy chunks
   b. Retrieve associated rules
   c. Use LLM to determine if chunk violates rules
   d. If violation detected, store in Violation table
5. Generate remediation suggestions for violations
6. Return audit summary
```

**LLM Violation Detection Prompt**:
```
You are a compliance auditor. Determine if the following document excerpt violates any compliance rules.

Document Excerpt:
{document_chunk}

Compliance Rules:
{rules}

Does this excerpt violate any rules? Respond in JSON:
{
  "violation_detected": true/false,
  "violated_rules": [rule_ids],
  "explanation": "...",
  "severity": "low/medium/high/critical"
}
```

**API Endpoints**:
```python
POST /api/audits/upload
GET /api/audits
GET /api/audits/{audit_id}
GET /api/audits/{audit_id}/violations
```

#### 7. Remediation Module (`app/remediation/`)

**Purpose**: Generate AI-powered remediation suggestions for violations

**Key Classes**:
- `RemediationService`: LLM-based suggestion generator

**LLM Remediation Prompt**:
```
You are a compliance consultant. Provide actionable remediation steps for the following violation.

Violation:
- Rule: {rule_text}
- Document Excerpt: {document_excerpt}
- Explanation: {violation_explanation}

Provide 3-5 specific, actionable steps to remediate this violation.
```

**API Endpoints**:
```python
POST /api/remediation/generate/{violation_id}
```

#### 8. Export Module (`app/exports/`)

**Purpose**: Generate PDF and CSV reports of audit results

**Key Classes**:
- `ExportService`: Report generation using Pandas and ReportLab/WeasyPrint

**CSV Export** (using Pandas):
```python
columns = ['Violation ID', 'Document', 'Rule', 'Severity', 'Date', 'Remediation']
df = pd.DataFrame(violations_data, columns=columns)
df.to_csv(output_path, index=False)
```

**PDF Export**: Use ReportLab or WeasyPrint to generate formatted reports

**API Endpoints**:
```python
GET /api/exports/csv/{audit_id}
GET /api/exports/pdf/{audit_id}
```

### Frontend Components

#### 1. Authentication Pages (`src/pages/auth/`)

**Components**:
- `LoginPage`: Email/password form, JWT token storage in localStorage
- `RegisterPage`: User registration form

**State Management**: React Query for API calls, Context API for auth state

#### 2. Dashboard Layout (`src/components/layout/`)

**Components**:
- `DashboardLayout`: Sidebar navigation, header with user menu
- `Sidebar`: Links to Policies, Audits, Violations, Settings

#### 3. Policy Management (`src/pages/policies/`)

**Components**:
- `PoliciesPage`: List of uploaded policies with upload button
- `PolicyUploadModal`: File upload form with drag-and-drop
- `PolicyCard`: Display policy metadata, status, actions

**API Integration**: React Query mutations for uploads, queries for list

#### 4. Audit Management (`src/pages/audits/`)

**Components**:
- `AuditsPage`: List of audit documents
- `AuditUploadModal`: Document upload form
- `AuditDetailPage`: Audit summary with violations count

#### 5. Violations Dashboard (`src/pages/violations/`)

**Components**:
- `ViolationsTable`: Sortable, filterable table using TanStack Table
- `ViolationDetailModal`: Show policy excerpt, document excerpt, remediation
- `ViolationFilters`: Filter by severity, date, document

**Table Columns**: Severity badge, Rule description, Document name, Date, Actions

#### 6. Export Controls (`src/components/exports/`)

**Components**:
- `ExportButton`: Dropdown for CSV/PDF export options
- Uses browser download API for file downloads

## Data Models

### PostgreSQL Schema

```sql
-- Users and Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Policies
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    filename VARCHAR(255) NOT NULL,
    s3_path VARCHAR(512) NOT NULL,
    upload_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'processing',
    file_size INTEGER,
    INDEX idx_org_policies (organization_id)
);

CREATE TABLE policy_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    INDEX idx_policy_chunks (policy_id)
);

-- Rules
CREATE TABLE compliance_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    policy_id UUID REFERENCES policies(id),
    rule_text TEXT NOT NULL,
    category VARCHAR(100),
    severity VARCHAR(20),
    source_chunk_id UUID REFERENCES policy_chunks(id),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_org_rules (organization_id)
);

-- Audits
CREATE TABLE audit_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    filename VARCHAR(255) NOT NULL,
    s3_path VARCHAR(512) NOT NULL,
    upload_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'processing',
    INDEX idx_org_audits (organization_id)
);

CREATE TABLE violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_document_id UUID REFERENCES audit_documents(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES compliance_rules(id),
    chunk_id UUID,
    severity VARCHAR(20),
    explanation TEXT,
    remediation TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_audit_violations (audit_document_id),
    INDEX idx_severity (severity)
);
```

### ChromaDB Collections

**Collection Naming**: `org_{organization_id}_policies`

**Document Structure**:
```python
{
    "id": "chunk_{chunk_id}",
    "embedding": [0.123, 0.456, ...],  # 1536-dim vector
    "metadata": {
        "chunk_id": "uuid",
        "policy_id": "uuid",
        "chunk_index": 0,
        "content_preview": "first 200 chars..."
    }
}
```

## Error Handling

### Backend Error Handling

**Exception Hierarchy**:
```python
class ComplianceAuditorException(Exception):
    """Base exception"""
    pass

class DocumentParsingError(ComplianceAuditorException):
    """PDF parsing failures"""
    pass

class EmbeddingGenerationError(ComplianceAuditorException):
    """Embedding API failures"""
    pass

class LLMAPIError(ComplianceAuditorException):
    """LLM API failures"""
    pass
```

**Error Response Format**:
```json
{
    "error": {
        "code": "DOCUMENT_PARSING_ERROR",
        "message": "Failed to parse PDF document",
        "details": "..."
    }
}
```

**Retry Logic**:
- Embedding generation: 3 retries with exponential backoff
- LLM API calls: 3 retries with exponential backoff
- S3 uploads: 2 retries

**Logging**: Use structlog for structured JSON logging
```python
logger.info("policy_uploaded", policy_id=policy_id, org_id=org_id, filename=filename)
logger.error("embedding_failed", policy_id=policy_id, error=str(e))
```

### Frontend Error Handling

**Error Boundaries**: Wrap main app sections to catch React errors

**API Error Handling**:
```typescript
const { data, error, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: fetchPolicies,
    onError: (error) => {
        toast.error(`Failed to load policies: ${error.message}`)
    }
})
```

**Toast Notifications**: Use react-hot-toast for user-facing error messages

## Testing Strategy

### Backend Testing

**Unit Tests** (pytest):
- Test individual functions in isolation
- Mock external dependencies (S3, ChromaDB, LLM APIs)
- Test cases:
  - `test_document_parser_extracts_text()`
  - `test_text_chunker_creates_500_token_chunks()`
  - `test_embedding_service_handles_api_errors()`
  - `test_rule_classifier_parses_llm_response()`

**Integration Tests**:
- Test API endpoints with test database
- Use pytest fixtures for database setup/teardown
- Test cases:
  - `test_policy_upload_flow()`
  - `test_audit_pipeline_detects_violations()`
  - `test_multi_tenant_isolation()`

**Test Database**: Use PostgreSQL test container or SQLite in-memory

### Frontend Testing

**Component Tests** (Vitest + React Testing Library):
- Test component rendering and user interactions
- Mock API calls with MSW (Mock Service Worker)
- Test cases:
  - `test_login_form_submits_credentials()`
  - `test_policy_upload_shows_progress()`
  - `test_violations_table_filters_by_severity()`

**E2E Tests** (Playwright - optional for MVP):
- Test critical user flows
- Test cases:
  - `test_user_can_upload_policy_and_view_rules()`
  - `test_user_can_audit_document_and_view_violations()`

### Testing Priorities for 10-Day MVP

Focus on:
1. Critical path integration tests (upload → parse → embed → audit)
2. Authentication and multi-tenant isolation tests
3. API endpoint tests for main features
4. Basic component tests for key UI elements

Defer:
- Comprehensive unit test coverage
- E2E tests
- Performance tests

## Deployment Architecture

### Docker Setup

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/compliance_db
      - CHROMA_HOST=chromadb
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - chromadb
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=compliance_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  postgres_data:
  chroma_data:
```

### CI/CD Pipeline (GitHub Actions)

**Workflow**:
1. Run linting (ruff for Python, eslint for TypeScript)
2. Run tests (pytest, vitest)
3. Build Docker images
4. Push to container registry
5. Deploy to staging/production

### Environment Variables

**Backend (.env)**:
```
DATABASE_URL=postgresql://...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=compliance-auditor-docs
OPENAI_API_KEY=...
GROQ_API_KEY=...
JWT_SECRET=...
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

**Frontend (.env)**:
```
VITE_API_URL=http://localhost:8000
```

### Health Checks

**Backend Health Endpoint**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_db_connection(),
        "chromadb": check_chroma_connection(),
        "s3": check_s3_connection()
    }
```

## Security Considerations

1. **Authentication**: JWT tokens with short expiration (1 hour), refresh token pattern
2. **Password Storage**: bcrypt hashing with salt
3. **SQL Injection**: Use SQLAlchemy ORM with parameterized queries
4. **CORS**: Configure allowed origins for frontend
5. **File Upload**: Validate file types, scan for malware (optional), limit file sizes
6. **API Rate Limiting**: Implement rate limiting on sensitive endpoints
7. **Environment Secrets**: Never commit secrets, use environment variables
8. **S3 Security**: Use IAM roles, presigned URLs with expiration
9. **Multi-Tenant Isolation**: Enforce organization_id filtering at middleware level

## Performance Considerations

1. **Async Processing**: Use FastAPI async endpoints for I/O operations
2. **Background Tasks**: Use Celery or FastAPI BackgroundTasks for long-running jobs (embedding generation, audits)
3. **Caching**: Cache frequently accessed data (rules, policy metadata) using Redis (optional for MVP)
4. **Database Indexing**: Index foreign keys and frequently queried columns
5. **Batch Processing**: Process embeddings and LLM calls in batches
6. **Frontend Optimization**: Code splitting, lazy loading, React Query caching

## Future Enhancements (Post-MVP)

1. **Analytics Dashboard**: Use Matplotlib/Plotly for visualization of compliance trends
2. **Real-time Notifications**: WebSocket support for audit progress updates
3. **Advanced Search**: Full-text search using PostgreSQL or Elasticsearch
4. **Audit Scheduling**: Periodic re-auditing of documents
5. **Custom Rule Creation**: UI for manual rule definition
6. **Integration APIs**: Webhooks for third-party integrations
7. **Mobile App**: React Native mobile client
