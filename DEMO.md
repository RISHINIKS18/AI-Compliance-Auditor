# AI Compliance Auditor - Demo Walkthrough

This guide provides a complete walkthrough of the AI Compliance Auditor system with sample data and expected results.

## Table of Contents

1. [Demo Overview](#demo-overview)
2. [Prerequisites](#prerequisites)
3. [Demo Scenario](#demo-scenario)
4. [Step-by-Step Walkthrough](#step-by-step-walkthrough)
5. [Expected Results](#expected-results)
6. [Sample Data](#sample-data)

## Demo Overview

This demo demonstrates the complete compliance auditing workflow:
1. User registration and authentication
2. Policy document upload and processing
3. Compliance rule extraction
4. Document audit with violation detection
5. Remediation suggestions
6. Report export

**Estimated Time**: 15-20 minutes

## Prerequisites

- System deployed and running (see [DEPLOYMENT.md](DEPLOYMENT.md))
- Backend accessible at `http://localhost:8000`
- Frontend accessible at `http://localhost:3000`
- Sample documents prepared (see [Sample Data](#sample-data) section)

## Demo Scenario

**Company**: TechCorp Inc.
**Scenario**: TechCorp has a data privacy policy and needs to audit employee communications for compliance violations.

**Documents**:
- **Policy**: Data Privacy and Security Policy (defines rules about data handling)
- **Audit Document**: Employee email communication (may contain violations)

## Step-by-Step Walkthrough

### Step 1: User Registration

**Action**: Create a new organization and user account

1. Navigate to `http://localhost:3000`
2. Click "Register" or "Sign Up"
3. Fill in registration form:
   - **Organization Name**: TechCorp Inc.
   - **Email**: admin@techcorp.com
   - **Password**: SecurePass123!
4. Click "Register"

**Expected Result**:
- User account created successfully
- Automatically logged in
- Redirected to dashboard

**API Call**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@techcorp.com",
    "password": "SecurePass123!",
    "organization_name": "TechCorp Inc."
  }'
```

**Expected Response**:
```json
{
  "id": "uuid-here",
  "email": "admin@techcorp.com",
  "organization_id": "org-uuid-here",
  "created_at": "2025-02-12T10:00:00Z"
}
```

### Step 2: Login (if needed)

**Action**: Authenticate with existing credentials

1. Navigate to `http://localhost:3000/login`
2. Enter credentials:
   - **Email**: admin@techcorp.com
   - **Password**: SecurePass123!
3. Click "Login"

**Expected Result**:
- JWT token stored in localStorage
- Redirected to dashboard

**API Call**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@techcorp.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "email": "admin@techcorp.com",
    "organization_id": "org-uuid-here"
  }
}
```

### Step 3: Upload Policy Document

**Action**: Upload the company's data privacy policy

1. Navigate to "Policies" page
2. Click "Upload Policy" button
3. Select file: `sample_data_privacy_policy.pdf`
4. Click "Upload"
5. Wait for processing to complete (status changes from "processing" to "completed")

**Expected Result**:
- Policy uploaded successfully
- File stored in S3 at path: `{org_id}/policies/{policy_id}.pdf`
- Policy metadata saved in database
- Background processing starts:
  - PDF parsed and text extracted
  - Text chunked into ~500 token segments
  - Embeddings generated for each chunk
  - Vectors stored in ChromaDB

**API Call**:
```bash
curl -X POST http://localhost:8000/api/policies/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@sample_data_privacy_policy.pdf"
```

**Expected Response**:
```json
{
  "id": "policy-uuid-here",
  "filename": "sample_data_privacy_policy.pdf",
  "organization_id": "org-uuid-here",
  "upload_date": "2025-02-12T10:05:00Z",
  "status": "processing",
  "file_size": 245678
}
```

**Processing Time**: 30-60 seconds depending on document size

### Step 4: Extract Compliance Rules

**Action**: Extract compliance rules from the uploaded policy

1. On the Policies page, find the uploaded policy
2. Click "Extract Rules" button
3. Wait for extraction to complete

**Expected Result**:
- LLM analyzes policy chunks
- Compliance rules extracted and classified
- Rules stored in database with:
  - Rule text/description
  - Category (e.g., "data privacy", "security")
  - Severity (low, medium, high, critical)
  - Source policy reference

**API Call**:
```bash
curl -X POST http://localhost:8000/api/rules/extract/{policy_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response**:
```json
{
  "policy_id": "policy-uuid-here",
  "rules_extracted": 12,
  "rules": [
    {
      "id": "rule-uuid-1",
      "rule_text": "Personal data must be encrypted at rest and in transit",
      "category": "data_security",
      "severity": "critical",
      "source_chunk_id": "chunk-uuid-1"
    },
    {
      "id": "rule-uuid-2",
      "rule_text": "Customer data must not be shared with third parties without explicit consent",
      "category": "data_privacy",
      "severity": "high",
      "source_chunk_id": "chunk-uuid-2"
    }
  ]
}
```

**Processing Time**: 1-2 minutes depending on policy size

### Step 5: View Extracted Rules

**Action**: Review the extracted compliance rules

1. Navigate to "Rules" page (or view in Policies detail)
2. Browse the list of extracted rules
3. Filter by category or severity

**Expected Result**:
- Table displaying all extracted rules
- Columns: Rule Description, Category, Severity, Source Policy
- Ability to filter and sort

### Step 6: Upload Document for Audit

**Action**: Upload an employee communication for compliance checking

1. Navigate to "Audits" page
2. Click "Upload Document" button
3. Select file: `sample_employee_email.pdf`
4. Click "Upload"
5. Wait for audit to complete

**Expected Result**:
- Document uploaded to S3
- Document parsed and chunked
- Embeddings generated
- For each chunk:
  - Similar policy chunks retrieved from ChromaDB
  - Associated compliance rules identified
  - LLM determines if violations exist
- Violations detected and stored
- Remediation suggestions generated

**API Call**:
```bash
curl -X POST http://localhost:8000/api/audits/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@sample_employee_email.pdf"
```

**Expected Response**:
```json
{
  "id": "audit-uuid-here",
  "filename": "sample_employee_email.pdf",
  "organization_id": "org-uuid-here",
  "upload_date": "2025-02-12T10:15:00Z",
  "status": "processing"
}
```

**Processing Time**: 1-3 minutes depending on document size

### Step 7: View Audit Results

**Action**: Check the audit summary

1. On the Audits page, click on the completed audit
2. View audit summary

**Expected Result**:
- Audit status: "completed"
- Total violations found: 3
- Severity breakdown:
  - Critical: 1
  - High: 1
  - Medium: 1
  - Low: 0

**API Call**:
```bash
curl -X GET http://localhost:8000/api/audits/{audit_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response**:
```json
{
  "id": "audit-uuid-here",
  "filename": "sample_employee_email.pdf",
  "status": "completed",
  "upload_date": "2025-02-12T10:15:00Z",
  "violations_summary": {
    "total": 3,
    "by_severity": {
      "critical": 1,
      "high": 1,
      "medium": 1,
      "low": 0
    }
  }
}
```

### Step 8: View Violations Dashboard

**Action**: Review detailed violations

1. Navigate to "Violations" page
2. View table of all violations
3. Filter by severity: "Critical"

**Expected Result**:
- Table showing all violations
- Columns: Severity, Rule Description, Document, Date
- Violations displayed with color-coded severity badges

**Example Violations**:

| Severity | Rule | Document | Date |
|----------|------|----------|------|
| 🔴 Critical | Personal data transmitted without encryption | sample_employee_email.pdf | 2025-02-12 |
| 🟠 High | Customer data shared without consent | sample_employee_email.pdf | 2025-02-12 |
| 🟡 Medium | Sensitive data stored in unsecured location | sample_employee_email.pdf | 2025-02-12 |

### Step 9: View Violation Details

**Action**: Examine a specific violation

1. Click on a violation row
2. View violation detail modal

**Expected Result**:
- **Policy Excerpt**: Relevant section from the policy
- **Document Excerpt**: The violating text from the audited document
- **Violation Explanation**: AI-generated explanation of why this is a violation
- **Remediation Suggestions**: Step-by-step guidance to fix the issue

**Example Violation Detail**:

```
Violation: Personal data transmitted without encryption

Policy Excerpt:
"All personal data, including customer names, email addresses, and phone numbers, 
must be encrypted using AES-256 encryption when transmitted over any network, 
including internal networks and email systems."

Document Excerpt:
"Hi team, here's the customer list for Q4:
- John Doe, john@email.com, 555-1234
- Jane Smith, jane@email.com, 555-5678
Please review and update the CRM system."

Explanation:
The email contains personal data (names, email addresses, phone numbers) that 
appears to be transmitted in plain text without encryption, violating the 
organization's data privacy policy.

Remediation Suggestions:
1. Remove personal data from the email immediately
2. Use secure file sharing system with encryption (e.g., encrypted SharePoint)
3. Implement email encryption (S/MIME or PGP) for sensitive communications
4. Train employees on proper handling of personal data
5. Implement DLP (Data Loss Prevention) tools to prevent future incidents
```

**API Call**:
```bash
curl -X GET http://localhost:8000/api/audits/{audit_id}/violations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Step 10: Export Audit Report

**Action**: Generate and download compliance report

1. On the Violations page or Audit detail page
2. Click "Export" button
3. Select format: "PDF" or "CSV"
4. Download the report

**Expected Result**:
- Report generated with all violations
- Includes policy references and remediation suggestions
- File downloaded to local machine

**API Calls**:

CSV Export:
```bash
curl -X GET http://localhost:8000/api/exports/csv/{audit_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o audit_report.csv
```

PDF Export:
```bash
curl -X GET http://localhost:8000/api/exports/pdf/{audit_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o audit_report.pdf
```

**CSV Format**:
```csv
Violation ID,Document,Rule,Severity,Category,Date,Remediation
uuid-1,sample_employee_email.pdf,"Personal data transmitted without encryption",Critical,data_security,2025-02-12,"1. Remove personal data from email..."
uuid-2,sample_employee_email.pdf,"Customer data shared without consent",High,data_privacy,2025-02-12,"1. Obtain explicit consent..."
```

### Step 11: Multi-Tenant Isolation Test (Optional)

**Action**: Verify data isolation between organizations

1. Logout from TechCorp account
2. Register a new organization: "CompetitorCorp"
3. Login with new account
4. Navigate to Policies page

**Expected Result**:
- No policies visible (TechCorp's policies are isolated)
- No violations visible
- Complete data separation between organizations

## Expected Results Summary

### Successful Demo Outcomes

✅ **User Registration**: New organization and user created
✅ **Authentication**: JWT token issued and stored
✅ **Policy Upload**: PDF uploaded to S3 and processed
✅ **Text Extraction**: Policy text extracted and chunked
✅ **Embeddings**: Vectors generated and stored in ChromaDB
✅ **Rule Extraction**: 10-15 compliance rules identified
✅ **Document Audit**: Audit document processed
✅ **Violation Detection**: 2-5 violations detected
✅ **Remediation**: AI-generated suggestions provided
✅ **Report Export**: PDF and CSV reports generated
✅ **Multi-Tenant**: Data isolation verified

### Performance Benchmarks

- **Policy Upload**: < 5 seconds
- **Policy Processing**: 30-90 seconds (depending on size)
- **Rule Extraction**: 1-3 minutes
- **Document Audit**: 1-3 minutes
- **Report Generation**: < 10 seconds

### Data Flow Verification

```
User Registration → JWT Token → Policy Upload → S3 Storage
                                      ↓
                                Text Extraction
                                      ↓
                                Text Chunking
                                      ↓
                              Embedding Generation
                                      ↓
                              ChromaDB Storage
                                      ↓
                              Rule Extraction (LLM)
                                      ↓
                              PostgreSQL Storage
                                      ↓
Document Upload → S3 Storage → Processing → Violation Detection
                                      ↓
                              Remediation Generation
                                      ↓
                              Dashboard Display
                                      ↓
                              Report Export
```

## Sample Data

### Sample Policy Document

Create a file named `sample_data_privacy_policy.pdf` with the following content:

```
TechCorp Inc. - Data Privacy and Security Policy

1. PURPOSE
This policy establishes requirements for handling personal and sensitive data 
to ensure compliance with data protection regulations and maintain customer trust.

2. SCOPE
This policy applies to all employees, contractors, and third-party vendors who 
handle customer data, employee data, or any other personal information.

3. DATA ENCRYPTION REQUIREMENTS
3.1 All personal data, including customer names, email addresses, phone numbers, 
    and payment information, MUST be encrypted using AES-256 encryption when 
    transmitted over any network.
3.2 Data at rest MUST be encrypted using industry-standard encryption methods.
3.3 Encryption keys MUST be stored separately from encrypted data and rotated 
    every 90 days.

4. DATA SHARING AND CONSENT
4.1 Customer data MUST NOT be shared with third parties without explicit written 
    consent from the customer.
4.2 Data sharing agreements MUST be reviewed by legal counsel before execution.
4.3 Customers MUST be notified within 72 hours of any data sharing activities.

5. DATA STORAGE AND RETENTION
5.1 Personal data MUST be stored in secure, access-controlled systems.
5.2 Data MUST NOT be stored on personal devices or unsecured cloud storage.
5.3 Customer data MUST be deleted within 30 days of account closure unless 
    required by law.

6. ACCESS CONTROLS
6.1 Access to personal data MUST be granted on a need-to-know basis.
6.2 All access to sensitive data MUST be logged and audited quarterly.
6.3 Multi-factor authentication MUST be enabled for all systems containing 
    personal data.

7. DATA BREACH RESPONSE
7.1 Any suspected data breach MUST be reported to the security team within 1 hour.
7.2 Affected customers MUST be notified within 72 hours of breach confirmation.
7.3 A post-incident review MUST be conducted within 7 days of breach resolution.

8. EMPLOYEE TRAINING
8.1 All employees MUST complete data privacy training within 30 days of hire.
8.2 Annual refresher training is REQUIRED for all staff.

9. COMPLIANCE AND AUDITING
9.1 Compliance audits MUST be conducted quarterly.
9.2 Non-compliance incidents MUST be documented and remediated within 14 days.

10. PENALTIES
Violations of this policy may result in disciplinary action up to and including 
termination of employment.
```

### Sample Audit Document (with violations)

Create a file named `sample_employee_email.pdf` with the following content:

```
From: john.employee@techcorp.com
To: team@techcorp.com
Date: February 10, 2025
Subject: Q4 Customer List - Please Review

Hi Team,

I'm sharing the Q4 customer list for your review. Please update the CRM system 
with any changes.

Customer List:
1. John Doe - john.doe@email.com - 555-1234 - Credit Card: 4532-****-****-1234
2. Jane Smith - jane.smith@email.com - 555-5678 - Credit Card: 4532-****-****-5678
3. Bob Johnson - bob.j@email.com - 555-9012 - Credit Card: 4532-****-****-9012

I've also attached the full customer database to my personal Dropbox for backup:
https://dropbox.com/personal/customer_data.xlsx

Let me know if you need anything else. I'll be sharing this list with our 
marketing partner, AdCorp, so they can run the Q1 campaign.

Thanks,
John
```

**Expected Violations in This Document**:

1. **Critical**: Personal data (names, emails, phone numbers, partial credit card numbers) transmitted in plain text email without encryption
2. **High**: Customer data being shared with third party (AdCorp) without explicit consent
3. **Medium**: Sensitive data stored in unsecured personal cloud storage (Dropbox)
4. **Medium**: Credit card information included in email (even if partially masked)

### Sample Compliant Document (no violations)

Create a file named `sample_compliant_email.pdf` with the following content:

```
From: sarah.employee@techcorp.com
To: team@techcorp.com
Date: February 11, 2025
Subject: Q4 Customer Review Process

Hi Team,

Please access the Q4 customer data through our secure portal:
https://secure.techcorp.com/customer-portal

All customer information is encrypted and access is logged per our data privacy policy.

For the Q1 marketing campaign, please submit a data sharing request through the 
legal portal. We'll need customer consent before sharing any information with 
external partners.

Thanks,
Sarah
```

**Expected Result**: No violations detected

## Testing Different Scenarios

### Scenario 1: Multiple Policies

Upload multiple policy documents:
- Data Privacy Policy
- Information Security Policy
- HR Policy

Expected: Rules extracted from all policies and applied during audits

### Scenario 2: Severity Filtering

1. Upload documents with varying violation severities
2. Use dashboard filters to view only "Critical" violations
3. Verify filtering works correctly

### Scenario 3: Multi-Tenant Isolation

1. Create two organizations
2. Upload different policies to each
3. Verify each organization only sees their own data

### Scenario 4: Error Handling

1. Upload corrupted PDF
2. Expected: Error message displayed, policy marked as "failed"
3. Upload non-PDF file
4. Expected: Validation error before upload

### Scenario 5: Large Documents

1. Upload policy document > 50 pages
2. Verify chunking and processing completes successfully
3. Check performance metrics

## Demo Script for Presentation

**Introduction (2 minutes)**
- Explain the problem: Manual compliance checking is time-consuming and error-prone
- Introduce AI Compliance Auditor solution

**Live Demo (10 minutes)**
1. Show registration and login (1 min)
2. Upload policy document (1 min)
3. Show rule extraction results (2 min)
4. Upload audit document (1 min)
5. Show violations dashboard (3 min)
6. Demonstrate remediation suggestions (2 min)

**Export and Reporting (2 minutes)**
- Generate PDF report
- Show CSV export
- Highlight key features

**Q&A (5 minutes)**
- Answer questions about architecture
- Discuss scalability and customization
- Address security concerns

## Troubleshooting Demo Issues

### Issue: Policy Processing Stuck

**Solution**: Check backend logs for errors
```bash
docker-compose logs -f backend
```

### Issue: No Rules Extracted

**Solution**: Verify LLM API key is configured correctly in backend/.env

### Issue: Violations Not Detected

**Solution**: 
- Ensure rules were extracted successfully
- Check ChromaDB connection
- Verify embeddings were generated

### Issue: Export Fails

**Solution**: Check backend logs for Pandas or ReportLab errors

## Next Steps After Demo

1. Customize policies for your organization
2. Integrate with existing document management systems
3. Set up automated auditing workflows
4. Configure alerts for critical violations
5. Train team on using the system

## Support

For demo support or questions:
- Check system health: `curl http://localhost:8000/health`
- Review logs: `docker-compose logs -f`
- Consult API docs: `http://localhost:8000/docs`
