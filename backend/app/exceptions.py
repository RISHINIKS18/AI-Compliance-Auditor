"""Custom exception classes for the AI Compliance Auditor."""


class ComplianceAuditorException(Exception):
    """Base exception for all compliance auditor errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class DocumentParsingError(ComplianceAuditorException):
    """Exception raised when document parsing fails."""
    pass


class EmbeddingGenerationError(ComplianceAuditorException):
    """Exception raised when embedding generation fails."""
    pass


class LLMAPIError(ComplianceAuditorException):
    """Exception raised when LLM API calls fail."""
    pass


class VectorStoreError(ComplianceAuditorException):
    """Exception raised when vector store operations fail."""
    pass


class S3StorageError(ComplianceAuditorException):
    """Exception raised when S3 storage operations fail."""
    pass


class RuleExtractionError(ComplianceAuditorException):
    """Exception raised when rule extraction fails."""
    pass


class ViolationDetectionError(ComplianceAuditorException):
    """Exception raised when violation detection fails."""
    pass


class RemediationGenerationError(ComplianceAuditorException):
    """Exception raised when remediation generation fails."""
    pass


class ExportGenerationError(ComplianceAuditorException):
    """Exception raised when report export generation fails."""
    pass
