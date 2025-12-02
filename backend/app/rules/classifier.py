"""
Rule classifier service for extracting compliance rules using LLM.
"""
import os
import time
import json
from typing import List, Dict, Any, Optional
import openai
import structlog

logger = structlog.get_logger()


class RuleClassifier:
    """
    Service for extracting compliance rules from policy text using LLM.
    """
    
    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.max_retries = 3
        self.base_delay = 1  # seconds
        
        logger.info(
            "rule_classifier_initialized",
            model=self.model
        )
    
    def extract_rules(
        self,
        policy_text: str,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract compliance rules from policy text using LLM.
        
        Args:
            policy_text: The policy text to analyze
            context: Optional additional context from similar policy chunks
            
        Returns:
            List of extracted rules with structure:
            [
                {
                    "rule_text": "...",
                    "category": "...",
                    "severity": "..."
                }
            ]
        """
        prompt = self._build_extraction_prompt(policy_text, context)
        
        logger.info(
            "extracting_rules",
            text_length=len(policy_text),
            has_context=context is not None
        )
        
        try:
            rules = self._call_llm_with_retry(prompt)
            
            logger.info(
                "rules_extracted",
                count=len(rules)
            )
            
            return rules
            
        except Exception as e:
            logger.error(
                "rule_extraction_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []
    
    def _build_extraction_prompt(
        self,
        policy_text: str,
        context: Optional[str] = None
    ) -> str:
        """
        Build the LLM prompt for rule extraction.
        
        Args:
            policy_text: The policy text to analyze
            context: Optional additional context
            
        Returns:
            Formatted prompt string
        """
        prompt = """You are a compliance expert. Extract specific, actionable compliance rules from the following policy text.

Policy Text:
{policy_text}
"""
        
        if context:
            prompt += """
Related Context:
{context}
"""
        
        prompt += """
For each rule you identify, provide:
1. Rule description (clear, specific requirement that can be checked)
2. Category (e.g., data_privacy, financial, hr, security, operational, legal)
3. Severity (low, medium, high, critical)

Guidelines:
- Only extract explicit, actionable rules that can be verified
- Focus on requirements, prohibitions, and obligations
- Ignore general statements or background information
- Each rule should be specific enough to check compliance against
- If no clear rules are present, return an empty array

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "rule_text": "specific requirement or prohibition",
    "category": "category_name",
    "severity": "low|medium|high|critical"
  }}
]

Do not include any explanation or text outside the JSON array."""
        
        formatted_prompt = prompt.format(
            policy_text=policy_text,
            context=context if context else ""
        )
        
        return formatted_prompt
    
    def _call_llm_with_retry(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Call LLM API with exponential backoff retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            List of extracted rules
            
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
                            "content": "You are a compliance expert that extracts structured compliance rules from policy documents. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=2000
                )
                
                # Extract and parse JSON response
                content = response.choices[0].message.content.strip()
                
                # Try to extract JSON if wrapped in markdown code blocks
                if content.startswith("```"):
                    # Remove markdown code block markers
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                    content = content.replace("```json", "").replace("```", "").strip()
                
                rules = json.loads(content)
                
                # Validate structure
                if not isinstance(rules, list):
                    logger.warning(
                        "invalid_response_structure",
                        response_type=type(rules).__name__
                    )
                    return []
                
                # Validate each rule has required fields
                validated_rules = []
                for rule in rules:
                    if isinstance(rule, dict) and "rule_text" in rule:
                        # Ensure all fields exist with defaults
                        validated_rule = {
                            "rule_text": rule.get("rule_text", ""),
                            "category": rule.get("category", "general"),
                            "severity": rule.get("severity", "medium")
                        }
                        validated_rules.append(validated_rule)
                
                return validated_rules
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        "rate_limit_hit_retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "rate_limit_max_retries_exceeded",
                        error=str(e)
                    )
                    raise
                    
            except openai.APIError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        "api_error_retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "api_error_max_retries_exceeded",
                        error=str(e)
                    )
                    raise
                    
            except json.JSONDecodeError as e:
                logger.error(
                    "json_parse_error",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    # Return empty list if JSON parsing fails after all retries
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
        
        raise Exception("Failed to extract rules after all retries")


# Global instance
rule_classifier = RuleClassifier()
