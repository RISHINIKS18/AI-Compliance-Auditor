# Document Processing Module

This module handles parsing, chunking, and processing of policy documents.

## Components

### 1. DocumentParser (`parser.py`)
Extracts and cleans text from PDF documents using PyMuPDF.

**Features:**
- Extract text from PDF files (file path or bytes)
- Clean text (remove extra whitespace, normalize unicode)
- Error handling for corrupted/invalid PDFs
- Structured logging

**Usage:**
```python
from app.processing.parser import document_parser

# From file path
text = document_parser.extract_text("/path/to/file.pdf")

# From bytes
text = document_parser.extract_text_from_bytes(pdf_bytes, filename="policy.pdf")
```

### 2. TextChunker (`chunker.py`)
Splits text into token-sized chunks with overlap using tiktoken.

**Features:**
- 500-token chunks with 50-token overlap (configurable)
- Token counting using tiktoken (cl100k_base encoding)
- NumPy-based chunk statistics
- Efficient chunking algorithm

**Usage:**
```python
from app.processing.chunker import text_chunker

# Chunk text
chunks = text_chunker.chunk_text(text)

# Count tokens
token_count = text_chunker.count_tokens(text)

# Get statistics
stats = text_chunker.get_chunk_statistics(chunks)
```

### 3. ProcessingPipeline (`pipeline.py`)
Orchestrates the complete processing workflow.

**Features:**
- Download from S3
- Parse PDF
- Chunk text
- Store chunks in database
- Update policy status (processing → completed/failed)
- Error handling and rollback

**Usage:**
```python
from app.processing.pipeline import processing_pipeline

# Process a policy
success = processing_pipeline.process_policy(policy_id, db)

# Reprocess a failed policy
success = processing_pipeline.reprocess_policy(policy_id, db)
```

## Integration

The processing pipeline is automatically triggered as a background task when a policy is uploaded via the `/api/policies/upload` endpoint.

### New API Endpoints

**POST /api/policies/{policy_id}/reprocess**
- Manually trigger reprocessing of a policy
- Useful for failed policies or updates
- Returns 202 Accepted

## Error Handling

- `DocumentParsingError`: Raised when PDF parsing fails
- All errors are logged with structured logging
- Failed policies are marked with status="failed"
- Database transactions are rolled back on errors

## Database Schema

**PolicyChunk Table:**
- `id`: UUID primary key
- `policy_id`: Foreign key to policies table
- `chunk_index`: Integer index of chunk
- `content`: Text content of chunk
- `token_count`: Number of tokens in chunk

## Dependencies

- `pymupdf` (fitz): PDF text extraction
- `tiktoken`: Token counting
- `numpy`: Efficient numerical operations
- `structlog`: Structured logging

## Testing

To test the processing pipeline:

1. Install dependencies: `pip install -r requirements.txt`
2. Upload a policy via the API
3. Check policy status: `GET /api/policies/{policy_id}`
4. Verify chunks in database: `SELECT * FROM policy_chunks WHERE policy_id = '...'`

## Performance Considerations

- Background processing prevents blocking API responses
- Batch operations for chunk insertion
- Efficient token counting with tiktoken
- NumPy for statistical calculations
- Structured logging for monitoring

## Future Enhancements

- Support for additional file formats (DOCX, TXT)
- Parallel processing for large documents
- Caching of parsed content
- Progress tracking for long-running operations
