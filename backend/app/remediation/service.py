"""Remediation service for generating AI-powered remediation suggestions."""
import os
import time
import json
from typing import Optional
import openai
import structlog

from app.models.audit import Violation
from app.models.rule import ComplianceRule

logger = structlog.get_logger()


class RemediationService:
    """Service for generating AI-powered remediation suggestions for violations."""
    
    def __init__(self):
        """Initialize remediation service with OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.max_retries = 3
        self.base_delay = 1  # seconds
        
        logger.info(
            "remediation_service_initialized",
            model=self.model
        )
    
    def generate_suggestion(
        self,
        violation: Violation,
        rule: ComplianceRule,
        document_excerpt: str
    ) -> str:
        """
        Generate AI-powered remediation suggestion for a violation.
        
        Args:
            violation: The violation object containing explanation
            rule: The compliance rule that was violated
            document_excerpt: The relevant excerpt from the document
            
        Returns:
            Remediation suggestion text with actionable steps
        """
        prompt = self._build_remediation_prompt(
            rule_text=rule.rule_text,
            rule_category=rule.category,
            rule_severity=rule.severity,
            document_excerpt=document_excerpt,
            violation_explanation=violation.explanation
        )
        
        logger.info(
            "generating_remediation",
            violation_id=str(violation.id),
            rule_id=str(rule.id),
            severity=violation.severity
        )
        
        try:
            remediation = self._call_llm_with_retry(prompt)
            
            logger.info(
                "remediation_generated",
                violation_id=str(violation.id),
                remediation_length=len(remediation)
            )
            
            return remediation
            
        except Exception as e:
            logger.error(
                "remediation_generation_failed",
                violation_id=str(violation.id),
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Return generic template on failure
            return self._get_generic_remediation_template(rule, violation)
    
    def _build_remediation_prompt(
        self,
        rule_text: str,
        rule_category: str,
        rule_severity: str,
        document_excerpt: str,
        violation_explanation: str
    ) -> str:
        """
        Build the LLM prompt for remediation suggestion generation.
        
        Args:
            rule_text: The compliance rule that was violated
            rule_category: Category of the rule (e.g., data privacy, security)
            rule_severity: Severity level of the rule
            document_excerpt: The document text that violated the rule
            violation_explanation: Explanation of how the rule was violated
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a compliance consultant. Provide actionable remediation steps for the following compliance violation.

Violation Details:
- Rule: {rule_text}
- Category: {rule_category}
- Severity: {rule_severity}
- Explanation: {violation_explanation}

Document Excerpt:
{document_excerpt}

Provide 3-5 specific, actionable steps to remediate this violation. Each step should be:
1. Clear and specific
2. Directly address the violation
3. Practical and implementable
4. Focused on compliance resolution

Format your response as a numbered list of remediation steps. Be concise but thorough.
Do not include any preamble or conclusion, just the numbered steps."""
        
        return prompt
    
    def _call_llm_with_retry(self, prompt: str) -> str:
        """
        Call LLM API with exponential backoff retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Remediation suggestion text
            
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
                            "content": "You are a compliance consultant that provides clear, actionable remediation steps for compliance violations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Low temperature for consistent, focused suggestions
                    max_tokens=1000
                )
                
                # Extract remediation text
                remediation = response.choices[0].message.content.strip()
                
                if not remediation:
                    logger.warning("empty_remediation_response", attempt=attempt + 1)
                    if attempt < self.max_retries - 1:
                        time.sleep(self.base_delay * (2 ** attempt))
                        continue
                    else:
                        raise Exception("Empty remediation response from LLM")
                
                return remediation
                
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
        
        raise Exception("Failed to generate remediation after all retries")
    
    def _get_generic_remediation_template(
        self,
        rule: ComplianceRule,
        violation: Violation
    ) -> str:
        """
        Provide a generic remediation template when LLM generation fails.
        
        Args:
            rule: The compliance rule that was violated
            violation: The violation object
            
        Returns:
            Generic remediation template text
        """
        severity_actions = {
            "critical": "immediate action and escalation to senior management",
            "high": "prompt action and review by compliance team",
            "medium": "timely review and corrective measures",
            "low": "review and documentation of corrective actions"
        }
        
        action_level = severity_actions.get(
            violation.severity.lower() if violation.severity else "medium",
            "appropriate corrective action"
        )
        
        template = f"""Generic Remediation Steps:

1. Review the compliance rule: {rule.rule_text}

2. Identify the specific content or practice that violates this rule in your document or process.

3. Consult with your compliance team or legal counsel to understand the full implications of this violation.

4. Develop a corrective action plan that addresses the violation and ensures future compliance with the rule.

5. Implement the corrective actions and document all changes made.

6. Conduct a follow-up review to verify that the violation has been fully remediated.

Note: This violation has been classified as {violation.severity} severity and requires {action_level}."""
        
        return template


# Global instance
remediation_service = RemediationService()
