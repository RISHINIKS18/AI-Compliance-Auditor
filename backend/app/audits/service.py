"""Audit service for violation detection."""
import os
import time
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import openai
import structlog

from app.models.audit import AuditDocument, Violation
from app.models.policy import PolicyChunk
from app.models.rule import ComplianceRule
from app.processing.parser import document_parser, DocumentParsingError
from app.processing.chunker import text_chunker
from app.services.s3 import s3_service
from app.embeddings.service import EmbeddingService
from app.embeddings.vector_store import VectorStore

logger = structlog.get_logger()


class ViolationDetector:
    """Service for detecting compliance violations in audit documents."""
    
    def __init__(self):
        """Initialize violation detector with required services."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.max_retries = 3
        self.base_delay = 1  # seconds
        
        logger.info(
            "violation_detector_initialized",
            model=self.model
        )
    
    def detect_violations(
        self,
        audit_chunk_content: str,
        audit_chunk_id: str,
        rules: List[ComplianceRule]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to determine if an audit chunk violates any compliance rules.
        
        Args:
            audit_chunk_content: The text content of the audit document chunk
            audit_chunk_id: ID of the audit chunk
            rules: List of compliance rules to check against
            
        Returns:
            List of detected violations with structure:
            [
                {
                    "rule_id": "...",
                    "violated": true,
                    "explanation": "...",
                    "severity": "..."
                }
            ]
        """
        if not rules:
            return []
        
        prompt = self._build_violation_detection_prompt(audit_chunk_content, rules)
        
        logger.info(
            "detecting_violations",
            chunk_length=len(audit_chunk_content),
            rules_count=len(rules)
        )
        
        try:
            violations = self._call_llm_with_retry(prompt)
            
            # Filter to only violated rules
            detected_violations = [v for v in violations if v.get("violated", False)]
            
            logger.info(
                "violations_detected",
                total_rules_checked=len(rules),
                violations_found=len(detected_violations)
            )
            
            return detected_violations
            
        except Exception as e:
            logger.error(
                "violation_detection_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []
    
    def _build_violation_detection_prompt(
        self,
        document_excerpt: str,
        rules: List[ComplianceRule]
    ) -> str:
        """
        Build the LLM prompt for violation detection.
        
        Args:
            document_excerpt: The document text to check
            rules: List of compliance rules
            
        Returns:
            Formatted prompt string
        """
        # Format rules for the prompt
        rules_text = ""
        for i, rule in enumerate(rules, 1):
            rules_text += f"\n{i}. [ID: {rule.id}] {rule.rule_text}\n"
            rules_text += f"   Category: {rule.category}, Severity: {rule.severity}\n"
        
        prompt = f"""You are a compliance auditor. Determine if the following document excerpt violates any of the provided compliance rules.

Document Excerpt:
{document_excerpt}

Compliance Rules to Check:
{rules_text}

For each rule, determine:
1. Whether the document excerpt violates the rule
2. If violated, provide a clear explanation of how it violates the rule
3. Assess the severity of the violation (use the rule's severity or adjust if needed)

Guidelines:
- Only flag violations if there is clear evidence in the document excerpt
- Be specific about what in the document violates the rule
- Consider context and intent, not just keywords
- If unsure, do not flag as a violation

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "rule_id": "uuid-of-rule",
    "violated": true,
    "explanation": "specific explanation of how the rule is violated",
    "severity": "low|medium|high|critical"
  }}
]

Only include rules that are violated. If no violations are found, return an empty array: []

Do not include any explanation or text outside the JSON array."""
        
        return prompt
    
    def _call_llm_with_retry(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Call LLM API with exponential backoff retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            List of violation results
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a compliance auditor that detects violations in documents. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,  # Low temperature for consistent detection
                    max_tokens=2000
                )
                
                # Extract and parse JSON response
                content = response.choices[0].message.content.strip()
                
                # Try to extract JSON if wrapped in markdown code blocks
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                    content = content.replace("```json", "").replace("```", "").strip()
                
                violations = json.loads(content)
                
                # Validate structure
                if not isinstance(violations, list):
                    logger.warning(
                        "invalid_response_structure",
                        response_type=type(violations).__name__
                    )
                    return []
                
                return violations
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        "rate_limit_hit_retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay
                    )
                    time.sleep(delay)
                else:
                    logger.error("rate_limit_max_retries_exceeded", error=str(e))
                    raise
                    
            except openai.APIError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        "api_error_retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay
                    )
                    time.sleep(delay)
                else:
                    logger.error("api_error_max_retries_exceeded", error=str(e))
                    raise
                    
            except json.JSONDecodeError as e:
                logger.error("json_parse_error", attempt=attempt + 1, error=str(e))
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    return []
                    
            except Exception as e:
                logger.error(
                    "llm_call_failed",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__
                )
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception("Failed to detect violations after all retries")


class AuditService:
    """Service for processing audit documents and detecting violations."""
    
    def __init__(self):
        """Initialize audit service."""
        self.violation_detector = ViolationDetector()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
    
    def process_audit(self, audit_id: str, db: Session) -> bool:
        """
        Process an audit document: parse, chunk, generate embeddings, and detect violations.
        
        Args:
            audit_id: UUID of the audit document to process
            db: Database session
            
        Returns:
            True if processing succeeded, False otherwise
        """
        # Fetch audit document from database
        audit = db.query(AuditDocument).filter(AuditDocument.id == audit_id).first()
        
        if not audit:
            logger.error("audit_not_found", audit_id=audit_id)
            return False
        
        logger.info(
            "processing_audit_started",
            audit_id=str(audit.id),
            filename=audit.filename,
            org_id=str(audit.organization_id)
        )
        
        try:
            # Update status to processing
            audit.status = "processing"
            db.commit()
            
            # Step 1: Download file from S3
            file_bytes = s3_service.download_file(audit.s3_path)
            
            if not file_bytes:
                raise Exception("Failed to download file from S3")
            
            logger.info(
                "audit_downloaded_from_s3",
                audit_id=str(audit.id),
                s3_path=audit.s3_path,
                file_size=len(file_bytes)
            )
            
            # Step 2: Parse PDF and extract text
            try:
                text_content = document_parser.extract_text_from_bytes(
                    file_bytes=file_bytes,
                    filename=audit.filename
                )
            except DocumentParsingError as e:
                logger.error(
                    "document_parsing_failed",
                    audit_id=str(audit.id),
                    error=str(e)
                )
                audit.status = "failed"
                db.commit()
                return False
            
            if not text_content or len(text_content.strip()) == 0:
                logger.error("no_text_extracted", audit_id=str(audit.id))
                audit.status = "failed"
                db.commit()
                return False
            
            logger.info(
                "text_extracted",
                audit_id=str(audit.id),
                text_length=len(text_content)
            )
            
            # Step 3: Chunk the text
            chunks = text_chunker.chunk_text(text_content)
            
            if not chunks:
                logger.error("no_chunks_created", audit_id=str(audit.id))
                audit.status = "failed"
                db.commit()
                return False
            
            stats = text_chunker.get_chunk_statistics(chunks)
            logger.info("text_chunked", audit_id=str(audit.id), **stats)
            
            # Step 4: Generate embeddings for audit chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.generate_embeddings(chunk_texts)
            
            if len(embeddings) != len(chunks):
                logger.error(
                    "embedding_count_mismatch",
                    audit_id=str(audit.id),
                    chunks=len(chunks),
                    embeddings=len(embeddings)
                )
                audit.status = "failed"
                db.commit()
                return False
            
            logger.info(
                "embeddings_generated",
                audit_id=str(audit.id),
                count=len(embeddings)
            )
            
            # Step 5: For each chunk, detect violations
            total_violations = 0
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                logger.info(
                    "processing_chunk",
                    audit_id=str(audit.id),
                    chunk_index=i,
                    total_chunks=len(chunks)
                )
                
                # Query ChromaDB for similar policy chunks
                search_results = self.vector_store.search(
                    organization_id=str(audit.organization_id),
                    query_embedding=embedding,
                    n_results=5  # Get top 5 similar policy chunks
                )
                
                # Extract chunk IDs from search results
                similar_chunk_ids = []
                if search_results and "ids" in search_results and len(search_results["ids"]) > 0:
                    # Remove "chunk_" prefix from IDs
                    similar_chunk_ids = [
                        chunk_id.replace("chunk_", "")
                        for chunk_id in search_results["ids"][0]
                    ]
                
                if not similar_chunk_ids:
                    logger.info(
                        "no_similar_chunks_found",
                        audit_id=str(audit.id),
                        chunk_index=i
                    )
                    continue
                
                # Retrieve associated compliance rules
                rules = db.query(ComplianceRule).filter(
                    ComplianceRule.source_chunk_id.in_(similar_chunk_ids),
                    ComplianceRule.organization_id == audit.organization_id
                ).all()
                
                if not rules:
                    logger.info(
                        "no_rules_found_for_chunks",
                        audit_id=str(audit.id),
                        chunk_index=i
                    )
                    continue
                
                logger.info(
                    "checking_rules",
                    audit_id=str(audit.id),
                    chunk_index=i,
                    rules_count=len(rules)
                )
                
                # Use LLM to determine if chunk violates rules
                violations = self.violation_detector.detect_violations(
                    audit_chunk_content=chunk.content,
                    audit_chunk_id=str(i),  # Use chunk index as ID
                    rules=rules
                )
                
                # Store detected violations
                for violation_data in violations:
                    violation = Violation(
                        audit_document_id=audit.id,
                        rule_id=violation_data.get("rule_id"),
                        chunk_id=None,  # We don't store audit chunks, just use index
                        severity=violation_data.get("severity", "medium"),
                        explanation=violation_data.get("explanation", ""),
                        remediation=None  # Will be generated in next task
                    )
                    db.add(violation)
                    total_violations += 1
                
                # Commit violations for this chunk
                db.commit()
            
            # Update audit status to completed
            audit.status = "completed"
            db.commit()
            
            logger.info(
                "audit_processing_completed",
                audit_id=str(audit.id),
                chunks_processed=len(chunks),
                violations_found=total_violations,
                status="completed"
            )
            
            return True
            
        except Exception as e:
            # Rollback any database changes
            db.rollback()
            
            # Update audit status to failed
            try:
                audit.status = "failed"
                db.commit()
            except Exception as commit_error:
                logger.error(
                    "failed_to_update_audit_status",
                    audit_id=str(audit.id),
                    error=str(commit_error)
                )
            
            logger.error(
                "audit_processing_failed",
                audit_id=str(audit.id),
                error=str(e),
                error_type=type(e).__name__
            )
            
            return False


# Global instance
audit_service = AuditService()
