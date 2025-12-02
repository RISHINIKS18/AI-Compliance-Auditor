# Implementation Plan

- [x] 1. Set up project structure and infrastructure
  - Create backend directory with FastAPI project structure (app/, tests/, alembic/)
  - Create frontend directory with Vite + React + JavaScript setup
  - Create docker-compose.yml with PostgreSQL, ChromaDB, backend, and frontend services
  - Create Dockerfile for backend (Python 3.11+, install dependencies)
  - Create Dockerfile for frontend (Node 18+, build static assets)
  - Set up .env.example templates for both backend and frontend
  - Initialize Git repository with .gitignore for Python and Node
  - _Requirements: 10.1, 10.2, 10.6, 10.7_

- [x] 2. Set up database and migrations
  - Install SQLAlchemy and Alembic in backend
  - Create database connection module (app/database.py)
  - Create initial Alembic migration for organizations and users tables
  - Create migration for policies and policy_chunks tables
  - Create migration for compliance_rules table
  - Create migration for audit_documents and violations tables
  - Add database indexes for organization_id, policy_id, and audit_document_id
  - _Requirements: 10.6_

- [x] 3. Implement authentication and multi-tenant foundation
  - [x] 3.1 Create User and Organization models
    - Define SQLAlchemy models for User and Organization in app/auth/models.py
    - Add password hashing utilities using passlib with bcrypt
    - _Requirements: 1.1, 1.5_
  
  - [x] 3.2 Implement JWT authentication service
    - Create JWT token generation and validation functions using python-jose
    - Implement registration endpoint with password hashing
    - Implement login endpoint returning JWT token
    - Create authentication dependency for FastAPI routes
    - _Requirements: 1.2, 1.4_
  
  - [x] 3.3 Create multi-tenant middleware
    - Implement FastAPI dependency to extract organization_id from JWT
    - Create database query helper that auto-filters by organization_id
    - _Requirements: 1.3, 1.5_
  
  - [ ]* 3.4 Write authentication tests
    - Test user registration with valid and invalid data
    - Test login with correct and incorrect credentials
    - Test JWT token validation and expiration
    - Test multi-tenant data isolation
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 4. Implement frontend authentication
  - [x] 4.1 Set up React Router and authentication context
    - Install React Router, React Query, and axios
    - Create AuthContext for managing authentication state
    - Create ProtectedRoute component for route guarding
    - Set up axios interceptor for JWT token injection
    - _Requirements: 1.2_
  
  - [x] 4.2 Create login and registration pages
    - Create LoginPage component with email/password form
    - Create RegisterPage component with organization creation
    - Implement form validation using react-hook-form
    - Add error handling and toast notifications using react-hot-toast
    - Store JWT token in localStorage on successful login
    - _Requirements: 1.1, 1.2_
  
  - [x] 4.3 Create dashboard layout
    - Create DashboardLayout component with sidebar and header
    - Create Sidebar component with navigation links
    - Create Header component with user menu and logout
    - Set up Tailwind CSS configuration and ShadCN components
    - _Requirements: 1.2_

- [x] 5. Implement policy upload and storage
  - [x] 5.1 Create Policy models and S3 integration
    - Define SQLAlchemy models for Policy and PolicyChunk
    - Create S3 client wrapper using boto3 for file uploads
    - Implement organization-scoped S3 path generation (org_id/policies/file_id.pdf)
    - _Requirements: 2.2, 2.3, 2.6_
  
  - [x] 5.2 Implement policy upload API endpoint
    - Create POST /api/policies/upload endpoint accepting multipart/form-data
    - Validate file type (PDF only) and file size limits
    - Upload file to S3 with organization-scoped path
    - Save policy metadata to PostgreSQL
    - Return policy ID and success status
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 5.3 Implement policy retrieval endpoints
    - Create GET /api/policies endpoint with organization filtering
    - Create GET /api/policies/{policy_id} endpoint
    - Create DELETE /api/policies/{policy_id} endpoint with S3 cleanup
    - _Requirements: 2.6_
  
  - [ ]* 5.4 Write policy management tests
    - Test policy upload with valid PDF file
    - Test policy upload with invalid file type
    - Test policy retrieval filters by organization
    - Test policy deletion removes S3 file and database record
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 6. Implement frontend policy management
  - [x] 6.1 Create policy list page
    - Create PoliciesPage component displaying policy table
    - Use React Query to fetch policies from API
    - Display policy metadata (filename, upload date, status)
    - Add loading and error states
    - _Requirements: 2.6_
  
  - [x] 6.2 Create policy upload UI
    - Create PolicyUploadModal component with file input
    - Implement drag-and-drop file upload using react-dropzone
    - Show upload progress indicator
    - Display success/error messages
    - Refresh policy list after successful upload
    - _Requirements: 2.1, 2.5_

- [x] 7. Implement document parsing and chunking
  - [x] 7.1 Create document parser
    - Install PyMuPDF (fitz) for PDF text extraction
    - Create DocumentParser class with extract_text method
    - Implement text cleaning (remove extra whitespace, normalize)
    - Add error handling for corrupted or unsupported PDFs
    - _Requirements: 3.1, 3.2, 3.6_
  
  - [x] 7.2 Implement text chunking with token counting
    - Install tiktoken for token counting
    - Create TextChunker class with chunk_text method
    - Implement 500-token window chunking with 50-token overlap
    - Use NumPy for efficient token-size calculations
    - _Requirements: 3.3, 3.4_
  
  - [x] 7.3 Create processing pipeline
    - Create background task for policy processing
    - Trigger parsing and chunking after policy upload
    - Store chunks in PolicyChunk table with references to parent policy
    - Update policy status (processing → completed/failed)
    - _Requirements: 3.5, 3.6_
  
  - [ ]* 7.4 Write document processing tests
    - Test PDF text extraction with sample documents
    - Test text cleaning removes unwanted characters
    - Test chunking creates approximately 500-token chunks
    - Test error handling for corrupted PDFs
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 8. Implement embedding generation and vector storage
  - [x] 8.1 Set up ChromaDB client
    - Install chromadb Python client
    - Create VectorStore class wrapping ChromaDB operations
    - Implement organization-scoped collection creation (org_{org_id}_policies)
    - _Requirements: 4.6_
  
  - [x] 8.2 Implement embedding service
    - Install OpenAI Python SDK
    - Create EmbeddingService class with generate_embeddings method
    - Implement batch embedding generation (100 chunks at a time)
    - Add retry logic with exponential backoff for API failures
    - _Requirements: 4.1, 4.5_
  
  - [x] 8.3 Store embeddings in ChromaDB
    - Generate embeddings for policy chunks after chunking completes
    - Store vectors in ChromaDB with metadata (chunk_id, policy_id, chunk_index)
    - Use NumPy for cosine similarity verification
    - _Requirements: 4.2, 4.3_
  
  - [x] 8.4 Implement semantic search endpoint
    - Create POST /api/embeddings/search endpoint
    - Accept query text and return top-k similar chunks
    - Use ChromaDB similarity search with organization filtering
    - _Requirements: 4.4_
  
  - [ ]* 8.5 Write embedding tests
    - Test embedding generation with mock OpenAI API
    - Test ChromaDB storage and retrieval
    - Test organization-level collection isolation
    - Test retry logic for API failures
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 9. Implement compliance rule classification
  - [ ] 9.1 Create ComplianceRule model and endpoints
    - Define SQLAlchemy model for ComplianceRule
    - Create GET /api/rules endpoint with organization filtering
    - Create GET /api/rules/{rule_id} endpoint
    - _Requirements: 5.5_
  
  - [ ] 9.2 Implement LLM-based rule classifier
    - Install OpenAI or Groq SDK for LLM calls
    - Create RuleClassifier class with extract_rules method
    - Implement LLM prompt template for rule extraction
    - Parse JSON response from LLM
    - Add retry logic for LLM API failures
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [ ] 9.3 Create rule extraction pipeline
    - Create POST /api/rules/extract/{policy_id} endpoint
    - Retrieve policy chunks from database
    - For each chunk, query ChromaDB for similar context
    - Call LLM with chunk and context to extract rules
    - Store extracted rules in ComplianceRule table
    - Handle extraction failures gracefully
    - _Requirements: 5.1, 5.3, 5.5, 5.6_
  
  - [ ]* 9.4 Write rule classification tests
    - Test LLM prompt generation with sample policy text
    - Test JSON response parsing
    - Test rule storage in database
    - Test error handling for LLM API failures
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 10. Implement document audit pipeline
  - [ ] 10.1 Create AuditDocument and Violation models
    - Define SQLAlchemy models for AuditDocument and Violation
    - Add foreign key relationships to ComplianceRule
    - _Requirements: 6.5_
  
  - [ ] 10.2 Implement document upload for auditing
    - Create POST /api/audits/upload endpoint
    - Upload document to S3 with organization-scoped path
    - Save audit document metadata to PostgreSQL
    - Trigger background processing
    - _Requirements: 6.1, 6.2_
  
  - [ ] 10.3 Implement violation detection service
    - Create ViolationDetector class with detect_violations method
    - Parse and chunk audit document using existing pipeline
    - Generate embeddings for audit document chunks
    - For each chunk, query ChromaDB for similar policy chunks
    - Retrieve associated compliance rules
    - Use LLM to determine if chunk violates rules
    - Store detected violations in Violation table
    - _Requirements: 6.3, 6.4, 6.5_
  
  - [ ] 10.4 Create audit retrieval endpoints
    - Create GET /api/audits endpoint with organization filtering
    - Create GET /api/audits/{audit_id} endpoint returning summary
    - Create GET /api/audits/{audit_id}/violations endpoint
    - Return compliant status if no violations found
    - _Requirements: 6.6, 6.7_
  
  - [ ]* 10.5 Write audit pipeline tests
    - Test document upload and processing
    - Test violation detection with mock LLM responses
    - Test compliant document returns no violations
    - Test organization-level data isolation
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ] 11. Implement remediation suggestion generation
  - [ ] 11.1 Create remediation service
    - Create RemediationService class with generate_suggestion method
    - Implement LLM prompt template for remediation suggestions
    - Include violation context, policy rule, and document excerpt in prompt
    - Parse LLM response and extract actionable steps
    - _Requirements: 8.2, 8.3_
  
  - [ ] 11.2 Integrate remediation into audit pipeline
    - Generate remediation suggestions when violations are detected
    - Store remediation text in Violation table
    - Provide generic template if LLM generation fails
    - _Requirements: 8.1, 8.4, 8.5_
  
  - [ ] 11.3 Create remediation endpoint
    - Create POST /api/remediation/generate/{violation_id} endpoint
    - Allow manual regeneration of remediation suggestions
    - _Requirements: 8.4_
  
  - [ ]* 11.4 Write remediation tests
    - Test LLM prompt generation with violation data
    - Test remediation storage in database
    - Test fallback to generic template on failure
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 12. Implement violations dashboard
  - [ ] 12.1 Create violations table component
    - Install TanStack Table for React
    - Create ViolationsTable component with sortable columns
    - Display severity badge, rule description, document name, date
    - Implement client-side sorting and pagination
    - _Requirements: 7.1, 7.2_
  
  - [ ] 12.2 Implement violation filtering
    - Create ViolationFilters component with severity, date, document filters
    - Implement filter state management
    - Update table based on active filters
    - _Requirements: 7.5_
  
  - [ ] 12.3 Create violation detail modal
    - Create ViolationDetailModal component
    - Display policy excerpt and document excerpt side-by-side
    - Show AI-generated remediation suggestions prominently
    - Add action buttons (mark resolved, export, etc.)
    - _Requirements: 7.3, 7.4_
  
  - [ ] 12.4 Integrate with React Query
    - Use React Query for violations data fetching
    - Implement caching and automatic refetching
    - Add loading and error states
    - _Requirements: 7.6_

- [ ] 13. Implement audit report export
  - [ ] 13.1 Create CSV export functionality
    - Install Pandas in backend
    - Create ExportService class with generate_csv method
    - Format violations data into DataFrame with proper columns
    - Include violation details, policy references, remediation
    - Filter by organization_id
    - _Requirements: 9.2, 9.4_
  
  - [ ] 13.2 Create PDF export functionality
    - Install ReportLab or WeasyPrint for PDF generation
    - Create PDF template with header, violation table, and details
    - Include policy references and remediation suggestions
    - _Requirements: 9.3_
  
  - [ ] 13.3 Create export endpoints
    - Create GET /api/exports/csv/{audit_id} endpoint
    - Create GET /api/exports/pdf/{audit_id} endpoint
    - Return file stream with appropriate content-type headers
    - Handle export failures with error messages
    - _Requirements: 9.1, 9.5, 9.6_
  
  - [ ] 13.4 Create frontend export controls
    - Create ExportButton component with CSV/PDF dropdown
    - Trigger download using browser download API
    - Show loading indicator during export generation
    - Display error toast on failure
    - _Requirements: 9.1, 9.5_
  
  - [ ]* 13.5 Write export tests
    - Test CSV generation with sample violations data
    - Test PDF generation with sample violations data
    - Test organization-level data filtering
    - Test error handling for export failures
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 14. Implement logging and error handling
  - [ ] 14.1 Set up structured logging
    - Install structlog in backend
    - Configure JSON logging format
    - Add logging to all major operations (upload, parse, embed, audit)
    - Include context (org_id, user_id, policy_id) in log entries
    - _Requirements: 10.3_
  
  - [ ] 14.2 Implement global exception handling
    - Create custom exception classes (DocumentParsingError, EmbeddingGenerationError, LLMAPIError)
    - Add FastAPI exception handlers for custom exceptions
    - Return standardized error response format
    - Log all exceptions with full context
    - _Requirements: 10.4_
  
  - [ ] 14.3 Add frontend error boundaries
    - Create ErrorBoundary component for React
    - Wrap main app sections with error boundaries
    - Display user-friendly error messages
    - Log errors to console for debugging
    - _Requirements: 10.4_

- [ ] 15. Create health check and monitoring
  - [ ] 15.1 Implement health check endpoint
    - Create GET /health endpoint
    - Check PostgreSQL connection status
    - Check ChromaDB connection status
    - Check S3 connection status
    - Return overall health status and individual service statuses
    - _Requirements: 10.7_
  
  - [ ] 15.2 Add service startup validation
    - Validate all required environment variables on startup
    - Test database connection on startup
    - Test ChromaDB connection on startup
    - Fail fast with clear error messages if services unavailable
    - _Requirements: 10.7_

- [ ] 16. Set up CI/CD pipeline
  - [ ] 16.1 Create GitHub Actions workflow
    - Create .github/workflows/ci.yml file
    - Add Python linting step using ruff
    - Add JavaScript linting step using eslint
    - Add backend test step using pytest
    - Add frontend test step using vitest
    - _Requirements: 10.5_
  
  - [ ] 16.2 Add Docker build and push steps
    - Build backend Docker image in CI
    - Build frontend Docker image in CI
    - Push images to container registry (optional for MVP)
    - _Requirements: 10.1, 10.2_

- [ ] 17. Create deployment documentation and demo
  - [ ] 17.1 Write deployment guide
    - Document environment variable setup
    - Document Docker Compose deployment steps
    - Document database migration process
    - Document AWS S3 bucket setup
    - _Requirements: 10.1, 10.2_
  
  - [ ] 17.2 Create demo script and sample data
    - Prepare sample policy documents
    - Prepare sample audit documents with violations
    - Create demo walkthrough script
    - Document expected results for demo
    - _Requirements: All_
  
  - [ ] 17.3 Final integration testing
    - Test complete end-to-end flow: register → upload policy → extract rules → upload document → view violations → export report
    - Test multi-tenant isolation with multiple organizations
    - Test error scenarios and recovery
    - Verify all API endpoints return correct responses
    - _Requirements: All_
