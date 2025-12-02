# Sample Data for AI Compliance Auditor Demo

This directory contains sample documents for demonstrating the AI Compliance Auditor system.

## Files

### Policy Documents

1. **data_privacy_policy.txt** - Sample data privacy and security policy with compliance rules
2. **compliant_document.txt** - Sample document that follows all policy rules (no violations)
3. **violation_document.txt** - Sample document with multiple compliance violations

## Usage

These text files can be converted to PDF format for testing:

### Using LibreOffice (Command Line)
```bash
libreoffice --headless --convert-to pdf data_privacy_policy.txt
libreoffice --headless --convert-to pdf compliant_document.txt
libreoffice --headless --convert-to pdf violation_document.txt
```

### Using Online Converters
- Upload .txt files to any online text-to-PDF converter
- Download the resulting PDF files

### Using Python (if needed)
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def txt_to_pdf(txt_file, pdf_file):
    c = canvas.Canvas(pdf_file, pagesize=letter)
    with open(txt_file, 'r') as f:
        text = f.read()
    
    y = 750
    for line in text.split('\n'):
        if y < 50:
            c.showPage()
            y = 750
        c.drawString(50, y, line[:80])
        y -= 15
    
    c.save()

txt_to_pdf('data_privacy_policy.txt', 'data_privacy_policy.pdf')
txt_to_pdf('compliant_document.txt', 'compliant_document.pdf')
txt_to_pdf('violation_document.txt', 'violation_document.pdf')
```

## Expected Results

### data_privacy_policy.pdf
- **Processing Time**: 30-60 seconds
- **Expected Rules Extracted**: 12-15 rules
- **Categories**: data_security, data_privacy, access_control, incident_response

### violation_document.pdf
- **Processing Time**: 1-2 minutes
- **Expected Violations**: 3-4 violations
- **Severities**: 1 Critical, 1-2 High, 1 Medium

### compliant_document.pdf
- **Processing Time**: 1-2 minutes
- **Expected Violations**: 0 (compliant)
- **Result**: "No violations detected" message

## Demo Workflow

1. Upload `data_privacy_policy.pdf` as a policy document
2. Wait for processing and rule extraction
3. Upload `violation_document.pdf` for audit
4. Review detected violations and remediation suggestions
5. Upload `compliant_document.pdf` for audit
6. Verify no violations are detected
7. Export reports in PDF and CSV formats

## Customization

Feel free to modify these documents to test different scenarios:
- Add more policy rules
- Create documents with specific violations
- Test edge cases and error handling
