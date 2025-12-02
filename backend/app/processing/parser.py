"""Document parser for extracting text from PDF files."""
import re
from typing import Optional
import fitz  # PyMuPDF
import structlog

logger = structlog.get_logger()


class DocumentParsingError(Exception):
    """Exception raised when document parsing fails."""
    pass


class DocumentParser:
    """Parser for extracting and cleaning text from PDF documents."""
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            file_path: Path to the PDF file (can be local path or file-like object)
            
        Returns:
            Extracted and cleaned text content
            
        Raises:
            DocumentParsingError: If parsing fails or PDF is corrupted
        """
        try:
            # Open the PDF document
            doc = fitz.open(file_path)
            
            # Check if document is valid
            if doc.page_count == 0:
                raise DocumentParsingError("PDF document has no pages")
            
            # Extract text from all pages
            text_content = []
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(page_text)
                except Exception as e:
                    logger.warning(
                        "page_extraction_failed",
                        page_num=page_num,
                        error=str(e)
                    )
                    # Continue with other pages even if one fails
                    continue
            
            doc.close()
            
            if not text_content:
                raise DocumentParsingError("No text content could be extracted from PDF")
            
            # Combine all pages
            raw_text = "\n\n".join(text_content)
            
            # Clean the extracted text
            cleaned_text = self._clean_text(raw_text)
            
            logger.info(
                "document_parsed",
                pages=len(text_content),
                text_length=len(cleaned_text)
            )
            
            return cleaned_text
            
        except fitz.FileDataError as e:
            logger.error("corrupted_pdf", error=str(e))
            raise DocumentParsingError(f"Corrupted or invalid PDF file: {str(e)}")
        except fitz.FileNotFoundError as e:
            logger.error("pdf_not_found", error=str(e))
            raise DocumentParsingError(f"PDF file not found: {str(e)}")
        except DocumentParsingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error("unexpected_parsing_error", error=str(e), error_type=type(e).__name__)
            raise DocumentParsingError(f"Failed to parse PDF: {str(e)}")
    
    def extract_text_from_bytes(self, file_bytes: bytes, filename: Optional[str] = None) -> str:
        """
        Extract text content from PDF file bytes.
        
        Args:
            file_bytes: PDF file content as bytes
            filename: Optional filename for logging purposes
            
        Returns:
            Extracted and cleaned text content
            
        Raises:
            DocumentParsingError: If parsing fails or PDF is corrupted
        """
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            # Check if document is valid
            if doc.page_count == 0:
                raise DocumentParsingError("PDF document has no pages")
            
            # Extract text from all pages
            text_content = []
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(page_text)
                except Exception as e:
                    logger.warning(
                        "page_extraction_failed",
                        page_num=page_num,
                        filename=filename,
                        error=str(e)
                    )
                    # Continue with other pages even if one fails
                    continue
            
            doc.close()
            
            if not text_content:
                raise DocumentParsingError("No text content could be extracted from PDF")
            
            # Combine all pages
            raw_text = "\n\n".join(text_content)
            
            # Clean the extracted text
            cleaned_text = self._clean_text(raw_text)
            
            logger.info(
                "document_parsed_from_bytes",
                filename=filename,
                pages=len(text_content),
                text_length=len(cleaned_text)
            )
            
            return cleaned_text
            
        except fitz.FileDataError as e:
            logger.error("corrupted_pdf", filename=filename, error=str(e))
            raise DocumentParsingError(f"Corrupted or invalid PDF file: {str(e)}")
        except DocumentParsingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(
                "unexpected_parsing_error",
                filename=filename,
                error=str(e),
                error_type=type(e).__name__
            )
            raise DocumentParsingError(f"Failed to parse PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and normalizing.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline (paragraph breaks)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove any remaining excessive whitespace
        text = text.strip()
        
        # Normalize unicode characters (optional, helps with consistency)
        # Replace common unicode quotes and dashes
        text = text.replace('\u2018', "'").replace('\u2019', "'")  # Smart quotes
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # Smart double quotes
        text = text.replace('\u2013', '-').replace('\u2014', '-')  # En/em dashes
        
        return text


# Create a singleton instance for easy import
document_parser = DocumentParser()
