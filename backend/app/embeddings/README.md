# Embeddings Module

This module handles vector embeddings generation and semantic search using OpenAI embeddings and ChromaDB.

## Components

### VectorStore (`vector_store.py`)
- Wraps ChromaDB operations
- Manages organization-scoped collections (`org_{org_id}_policies`)
- Provides methods for adding, searching, and deleting embeddings

### EmbeddingService (`service.py`)
- Generates embeddings using OpenAI API
- Implements batch processing (100 chunks at a time)
- Includes retry logic with exponential backoff for API failures

### EmbeddingPipeline (`pipeline.py`)
- Orchestrates embedding generation for policy chunks
- Integrates with the document processing pipeline
- Verifies embeddings using NumPy cosine similarity

### API Routes (`routes.py`)
- `POST /api/embeddings/search` - Semantic search across policy chunks
- `POST /api/embeddings/generate/{policy_id}` - Manually trigger embedding generation

## Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Default model
EMBEDDING_BATCH_SIZE=100  # Batch size for embedding generation
CHROMA_HOST=chromadb  # ChromaDB host
CHROMA_PORT=8000  # ChromaDB port
```

## Usage

### Automatic Embedding Generation

Embeddings are automatically generated after policy documents are processed:

1. Policy uploaded → parsed → chunked
2. Chunks stored in PostgreSQL
3. Embeddings generated for all chunks
4. Embeddings stored in ChromaDB with metadata

### Manual Embedding Generation

```bash
curl -X POST http://localhost:8000/api/embeddings/generate/{policy_id} \
  -H "Authorization: Bearer {token}"
```

### Semantic Search

```bash
curl -X POST http://localhost:8000/api/embeddings/search \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "data privacy requirements",
    "n_results": 5,
    "policy_id": "optional-policy-id-filter"
  }'
```

## Multi-Tenant Isolation

- Each organization has its own ChromaDB collection: `org_{organization_id}_policies`
- All searches are automatically scoped to the user's organization
- Embeddings include organization metadata for additional filtering

## Error Handling

- API failures trigger exponential backoff retry (up to 3 attempts)
- Embedding generation failures don't block policy processing
- All errors are logged with structured logging

## Performance

- Batch processing reduces API calls
- ChromaDB provides fast similarity search
- NumPy used for efficient vector operations
