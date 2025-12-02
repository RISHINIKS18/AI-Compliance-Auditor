"""Export service for generating CSV and PDF reports."""
import io
from typing import Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models.audit import AuditDocument, Violation
from app.models.rule import ComplianceRule
from app.models.policy import Policy


class ExportService:
    """Service for generating audit report exports."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_csv(
        self,
        audit_id: str,
        organization_id: str
    ) -> tuple[io.BytesIO, str]:
        """
        Generate CSV export for audit violations.
        
        Args:
            audit_id: UUID of the audit document
            organization_id: UUID of the organization (for filtering)
            
        Returns:
            Tuple of (BytesIO buffer, filename)
            
        Raises:
            ValueError: If audit not found or doesn't belong to organization
        """
        # Verify audit belongs to organization
        audit = self.db.execute(
            select(AuditDocument)
            .where(
                AuditDocument.id == audit_id,
                AuditDocument.organization_id == organization_id
            )
        ).scalar_one_or_none()
        
        if not audit:
            raise ValueError("Audit document not found or access denied")
        
        # Fetch violations with related data
        violations_query = (
            select(
                Violation,
                ComplianceRule,
                Policy
            )
            .join(ComplianceRule, Violation.rule_id == ComplianceRule.id)
            .join(Policy, ComplianceRule.policy_id == Policy.id)
            .where(Violation.audit_document_id == audit_id)
            .order_by(Violation.detected_at.desc())
        )
        
        results = self.db.execute(violations_query).all()
        
        # Format data for CSV
        data = []
        for violation, rule, policy in results:
            data.append({
                'Violation ID': str(violation.id),
                'Document': audit.filename,
                'Severity': violation.severity,
                'Rule Description': rule.rule_text,
                'Rule Category': rule.category,
                'Policy Source': policy.filename,
                'Explanation': violation.explanation or '',
                'Remediation': violation.remediation or '',
                'Detected At': violation.detected_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Generate CSV in memory
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False, encoding='utf-8')
        buffer.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audit_report_{audit.filename}_{timestamp}.csv"
        
        return buffer, filename

    async def generate_pdf(
        self,
        audit_id: str,
        organization_id: str
    ) -> tuple[io.BytesIO, str]:
        """
        Generate PDF export for audit violations.
        
        Args:
            audit_id: UUID of the audit document
            organization_id: UUID of the organization (for filtering)
            
        Returns:
            Tuple of (BytesIO buffer, filename)
            
        Raises:
            ValueError: If audit not found or doesn't belong to organization
        """
        # Verify audit belongs to organization
        audit = self.db.execute(
            select(AuditDocument)
            .where(
                AuditDocument.id == audit_id,
                AuditDocument.organization_id == organization_id
            )
        ).scalar_one_or_none()
        
        if not audit:
            raise ValueError("Audit document not found or access denied")
        
        # Fetch violations with related data
        violations_query = (
            select(
                Violation,
                ComplianceRule,
                Policy
            )
            .join(ComplianceRule, Violation.rule_id == ComplianceRule.id)
            .join(Policy, ComplianceRule.policy_id == Policy.id)
            .where(Violation.audit_document_id == audit_id)
            .order_by(Violation.detected_at.desc())
        )
        
        results = self.db.execute(violations_query).all()
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12,
            spaceBefore=12
        )
        normal_style = styles['Normal']
        
        # Title
        story.append(Paragraph("Compliance Audit Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Audit Information
        audit_info = [
            ['Document:', audit.filename],
            ['Audit Date:', audit.upload_date.strftime('%Y-%m-%d %H:%M:%S')],
            ['Status:', audit.status],
            ['Total Violations:', str(len(results))]
        ]
        
        audit_table = Table(audit_info, colWidths=[2 * inch, 4 * inch])
        audit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db'))
        ]))
        
        story.append(audit_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Violations Section
        if results:
            story.append(Paragraph("Violations Details", heading_style))
            story.append(Spacer(1, 0.1 * inch))
            
            for idx, (violation, rule, policy) in enumerate(results, 1):
                # Violation header
                severity_color = self._get_severity_color(violation.severity)
                violation_header = f"<b>Violation #{idx}</b> - Severity: <font color='{severity_color}'><b>{violation.severity.upper()}</b></font>"
                story.append(Paragraph(violation_header, normal_style))
                story.append(Spacer(1, 0.1 * inch))
                
                # Violation details
                details = [
                    ['Rule:', rule.rule_text[:200] + ('...' if len(rule.rule_text) > 200 else '')],
                    ['Category:', rule.category or 'N/A'],
                    ['Policy Source:', policy.filename],
                    ['Detected:', violation.detected_at.strftime('%Y-%m-%d %H:%M:%S')]
                ]
                
                if violation.explanation:
                    details.append(['Explanation:', violation.explanation[:300] + ('...' if len(violation.explanation) > 300 else '')])
                
                details_table = Table(details, colWidths=[1.5 * inch, 4.5 * inch])
                details_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f9fafb')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb'))
                ]))
                
                story.append(details_table)
                story.append(Spacer(1, 0.1 * inch))
                
                # Remediation
                if violation.remediation:
                    story.append(Paragraph("<b>Remediation Suggestions:</b>", normal_style))
                    story.append(Spacer(1, 0.05 * inch))
                    remediation_text = violation.remediation[:500] + ('...' if len(violation.remediation) > 500 else '')
                    story.append(Paragraph(remediation_text, normal_style))
                
                # Add separator between violations
                if idx < len(results):
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph("<hr/>", normal_style))
                    story.append(Spacer(1, 0.2 * inch))
        else:
            story.append(Paragraph("<b>No violations detected. Document is compliant.</b>", normal_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audit_report_{audit.filename}_{timestamp}.pdf"
        
        return buffer, filename
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color code for severity level."""
        severity_colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#f59e0b',
            'low': '#84cc16'
        }
        return severity_colors.get(severity.lower(), '#6b7280')
