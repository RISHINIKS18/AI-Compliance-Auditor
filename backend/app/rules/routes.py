"""Compliance rule API routes."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.models.rule import ComplianceRule
from app.models.policy import Policy, PolicyChunk
from app.rules.schemas import (
    ComplianceRuleResponse,
    ComplianceRuleListResponse,
    RuleExtractionResponse
)
from app.rules.classifier import rule_classifier
from app.embeddings.service import EmbeddingService
from app.embeddings.vector_store import VectorStore

logger = structlog.get_logger()

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=ComplianceRuleListResponse)
async def get_rules(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    policy_id: uuid.UUID | None = None
):
    """
    Get all compliance rules for the current user's organization.
    
    Optionally filter by policy_id.
    Returns list of rules with metadata, filtered by organization.
    """
    query = db.query(ComplianceRule).filter(
        ComplianceRule.organization_id == current_user.organization_id
    )
    
    if policy_id:
        query = query.filter(ComplianceRule.policy_id == policy_id)
    
    rules = query.order_by(ComplianceRule.created_at.desc()).all()
    
    logger.info(
        "rules_retrieved",
        org_id=str(current_user.organization_id),
        policy_id=str(policy_id) if policy_id else None,
        count=len(rules)
    )
    
    return ComplianceRuleListResponse(
        rules=[ComplianceRuleResponse.model_validate(r) for r in rules],
        total=len(rules)
    )


@router.get("/{rule_id}", response_model=ComplianceRuleResponse)
async def get_rule(
    rule_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get a specific compliance rule by ID.
    
    Returns rule details if it belongs to the user's organization.
    """
    rule = db.query(ComplianceRule).filter(
        ComplianceRule.id == rule_id,
        ComplianceRule.organization_id == current_user.organization_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance rule not found"
        )
    
    logger.info(
        "rule_retrieved",
        rule_id=str(rule_id),
        org_id=str(current_user.organization_id)
    )
    
    return ComplianceRuleResponse.model_validate(rule)



def extract_rules_background(policy_id: str):
    """
    Background task to extract compliance rules from a policy.
    
    Args:
        policy_id: UUID of the policy to process
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        logger.info("rule_extraction_started", policy_id=policy_id)
        
        # Get policy and verify it exists
        policy = db.query(Policy).filter(Policy.id == uuid.UUID(policy_id)).first()
        if not policy:
            logger.error("policy_not_found", policy_id=policy_id)
            return
        
        # Get all chunks for this policy
        chunks = db.query(PolicyChunk).filter(
            PolicyChunk.policy_id == uuid.UUID(policy_id)
        ).order_by(PolicyChunk.chunk_index).all()
        
        if not chunks:
            logger.warning("no_chunks_found", policy_id=policy_id)
            return
        
        logger.info("chunks_retrieved", policy_id=policy_id, count=len(chunks))
        
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        
        rules_extracted = 0
        
        # Process each chunk
        for chunk in chunks:
            try:
                # Generate embedding for the chunk to find similar context
                chunk_embedding = embedding_service.generate_single_embedding(chunk.content)
                
                # Query ChromaDB for similar policy chunks (context)
                search_results = vector_store.search(
                    organization_id=str(policy.organization_id),
                    query_embedding=chunk_embedding,
                    n_results=3  # Get top 3 similar chunks for context
                )
                
                # Build context from similar chunks
                context = ""
                if search_results and search_results.get("documents"):
                    context_docs = search_results["documents"][0]  # First query results
                    context = "\n\n".join(context_docs[:2])  # Use top 2 for context
                
                # Extract rules using LLM
                extracted_rules = rule_classifier.extract_rules(
                    policy_text=chunk.content,
                    context=context if context else None
                )
                
                # Store extracted rules in database
                for rule_data in extracted_rules:
                    rule = ComplianceRule(
                        organization_id=policy.organization_id,
                        policy_id=policy.id,
                        rule_text=rule_data["rule_text"],
                        category=rule_data.get("category"),
                        severity=rule_data.get("severity"),
                        source_chunk_id=chunk.id
                    )
                    db.add(rule)
                    rules_extracted += 1
                
                # Commit after each chunk to avoid losing progress
                db.commit()
                
                logger.info(
                    "chunk_processed",
                    policy_id=policy_id,
                    chunk_id=str(chunk.id),
                    rules_found=len(extracted_rules)
                )
                
            except Exception as e:
                logger.error(
                    "chunk_processing_failed",
                    policy_id=policy_id,
                    chunk_id=str(chunk.id),
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Continue processing other chunks even if one fails
                continue
        
        logger.info(
            "rule_extraction_completed",
            policy_id=policy_id,
            total_rules_extracted=rules_extracted
        )
        
    except Exception as e:
        logger.error(
            "rule_extraction_exception",
            policy_id=policy_id,
            error=str(e),
            error_type=type(e).__name__
        )
    finally:
        db.close()


@router.post("/extract/{policy_id}", response_model=RuleExtractionResponse, status_code=status.HTTP_202_ACCEPTED)
async def extract_rules(
    policy_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Extract compliance rules from a policy document.
    
    This endpoint triggers background processing that:
    1. Retrieves policy chunks from database
    2. For each chunk, queries ChromaDB for similar context
    3. Calls LLM with chunk and context to extract rules
    4. Stores extracted rules in ComplianceRule table
    
    The extraction runs asynchronously in the background.
    """
    # Verify policy exists and belongs to user's organization
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.organization_id == current_user.organization_id
    ).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Check if policy has been processed (has chunks)
    chunk_count = db.query(PolicyChunk).filter(
        PolicyChunk.policy_id == policy_id
    ).count()
    
    if chunk_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy has not been processed yet. Please wait for processing to complete."
        )
    
    # Trigger background rule extraction
    background_tasks.add_task(
        extract_rules_background,
        policy_id=str(policy_id)
    )
    
    logger.info(
        "rule_extraction_triggered",
        policy_id=str(policy_id),
        org_id=str(current_user.organization_id)
    )
    
    return RuleExtractionResponse(
        policy_id=policy_id,
        rules_extracted=0,  # Will be updated by background task
        status="processing",
        message="Rule extraction started in background"
    )
