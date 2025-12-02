# AI Compliance Auditor - Integration Testing Guide

This guide provides comprehensive integration testing procedures for the AI Compliance Auditor system.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Prerequisites](#prerequisites)
3. [End-to-End Flow Testing](#end-to-end-flow-testing)
4. [Multi-Tenant Isolation Testing](#multi-tenant-isolation-testing)
5. [Error Scenario Testing](#error-scenario-testing)
6. [API Endpoint Verification](#api-endpoint-verification)
7. [Performance Testing](#performance-testing)
8. [Test Results Documentation](#test-results-documentation)

## Testing Overview

This testing guide covers:
- Complete end-to-end user workflows
- Multi-tenant data isolation
- Error handling and recovery
- API endpoint functionality
- System performance under load

**Estimated Testing Time**: 2-3 hours for complete test suite

## Prerequisites

### System Requirements
- System deployed and running (see DEPLOYMENT.md)
- Backend accessible at `http://localhost:8000`
- Frontend accessible at `http://localhost:3000`
- All services healthy (check `/health` endpoint)

### Testing Tools
```bash
# Install testing tools
pip install pytest requests
npm install -g newman  # For API testing
```

### Sample Data
- Ensure sample data files are available in `sample_data/` directory
- Convert .txt files to PDF format if needed

## End-to-End Flow Testing

### Test 1: Complete User Journey

**Objective**: Verify the complete workflow from registration to report export

**Steps**:

1. **User Registration**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "TestPass123!",
       "organization_name": "Test Organization"
     }'
   ```
   
   **Expected**: 
   - Status: 200 OK
   - Response contains user_id and organization_id
   - User can login with credentials

2. **User Login**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "TestPass123!"
     }'
   ```
   
   **Expected**:
   - Status: 200 OK
   - Response contains JWT access_token
   - Token is valid for API requests

3. **Upload Policy Document**
   ```bash
   TOKEN="your_jwt_token_here"
   curl -X POST http://localhost:8000/api/policies/upload \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@sample_data/data_privacy_policy.pdf"
   ```
   
   **Expected**:
   - Status: 200 OK
   - Policy uploaded to S3
   - Policy status: "processing"
   - Background processing initiated

4. **Wait for Policy Processing**
   ```bash
   POLICY_ID="policy_id_from_upload"
   curl -X GET http://localhost:8000/api/policies/$POLICY_ID \
     -H "Authorization: Bearer $TOKEN"
   ```
   
   **Expected**:
   - Status eventually changes to "completed"
   - Processing time: 30-90 seconds
   - Chunks created in database
   - Embeddings stored in ChromaDB

5. **Extract Compliance Rules**
   ```bash
   curl -X POST http://localhost:8000/api/rules/extract/$POLICY_ID \
     -H "Authorization: Bearer $TOKEN"
   ```
   
   **Expected**:
   - Status: 200 OK
   - 10-15 rules extracted
   - Rules have categories and severity levels
   - Rules stored in database

6. **Upload Document for Audit**
   ```bash
   curl -X POST http://localhost:8000/api/audits/upload \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@sample_data/violation_document.pdf"
   ```
   
   **Expected**:
   - Status: 200 OK
   - Document uploaded to S3
   - Audit status: "processing"
   - Background audit initiated

7. **Check Audit Results**
   ```bash
   AUDIT_ID="audit_id_from_upload"
   curl -X GET http://localhost:8000/api/audits/$AUDIT_ID \
     -H "Authorization: Bearer $TOKEN"
   ```
   
   **Expected**:
   - Status: "completed"
   - Violations detected: 3-5
   - Severity breakdown provided
   - Processing time: 1-3 minutes

8. **View Violations**
   ```bash
   curl -X GET http://localhost:8000/api/audits/$AUDIT_ID/violations \
     -H "Authorization: Bearer $TOKEN"
   ```
   
   **Expected**:
   - List of violations returned
   - Each violation includes:
     - Rule reference
     - Severity level
     - Document excerpt
     - Remediation suggestions

9. **Export Report (CSV)**
   ```bash
   curl -X GET http://localhost:8000/api/exports/csv/$AUDIT_ID \
     -H "Authorization: Bearer $TOKEN" \
     -o test_report.csv
   ```
   
   **Expected**:
   - Status: 200 OK
   - CSV file downloaded
   - Contains all violation data
   - Properly formatted

10. **Export Report (PDF)**
    ```bash
    curl -X GET http://localhost:8000/api/exports/pdf/$AUDIT_ID \
      -H "Authorization: Bearer $TOKEN" \
      -o test_report.pdf
    ```
    
    **Expected**:
    - Status: 200 OK
    - PDF file downloaded
    - Contains formatted report
    - Includes remediation suggestions

**Test Result**: ✅ PASS / ❌ FAIL

**Notes**: _____________________________________

### Test 2: Compliant Document (No Violations)

**Objective**: Verify system correctly identifies compliant documents

**Steps**:

1. Upload compliant document
   ```bash
   curl -X POST http://localhost:8000/api/audits/upload \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@sample_data/compliant_document.pdf"
   ```

2. Check audit results
   ```bash
   curl -X GET http://localhost:8000/api/audits/$AUDIT_ID \
     -H "Authorization: Bearer $TOKEN"
   ```

**Expected**:
- Status: "completed"
- Violations detected: 0
- Message: "No violations detected" or "Document is compliant"

**Test Result**: ✅ PASS / ❌ FAIL

## Multi-Tenant Isolation Testing

### Test 3: Data Isolation Between Organizations

**Objective**: Verify complete data isolation between different organizations

**Steps**:

1. **Create First Organization**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "org1@example.com",
       "password": "Pass123!",
       "organization_name": "Organization 1"
     }'
   ```
   
   Save TOKEN_ORG1

2. **Create Second Organization**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "org2@example.com",
       "password": "Pass123!",
       "organization_name": "Organization 2"
     }'
   ```
   
   Save TOKEN_ORG2

3. **Upload Policy to Org 1**
   ```bash
   curl -X POST http://localhost:8000/api/policies/upload \
     -H "Authorization: Bearer $TOKEN_ORG1" \
     -F "file=@sample_data/data_privacy_policy.pdf"
   ```
   
   Save POLICY_ID_ORG1

4. **Try to Access Org 1 Policy from Org 2**
   ```bash
   curl -X GET http://localhost:8000/api/policies/$POLICY_ID_ORG1 \
     -H "Authorization: Bearer $TOKEN_ORG2"
   ```
   
   **Expected**:
   - Status: 403 Forbidden or 404 Not Found
   - Error message about unauthorized access

5. **List Policies for Org 2**
   ```bash
   curl -X GET http://localhost:8000/api/policies \
     -H "Authorization: Bearer $TOKEN_ORG2"
   ```
   
   **Expected**:
   - Empty list or no Org 1 policies visible
   - Only Org 2 policies returned

6. **Upload Audit Document to Org 1**
   ```bash
   curl -X POST http://localhost:8000/api/audits/upload \
     -H "Authorization: Bearer $TOKEN_ORG1" \
     -F "file=@sample_data/violation_document.pdf"
   ```
   
   Save AUDIT_ID_ORG1

7. **Try to Access Org 1 Audit from Org 2**
   ```bash
   curl -X GET http://localhost:8000/api/audits/$AUDIT_ID_ORG1 \
     -H "Authorization: Bearer $TOKEN_ORG2"
   ```
   
   **Expected**:
   - Status: 403 Forbidden or 404 Not Found
   - No access to other organization's data

**Test Result**: ✅ PASS / ❌ FAIL

**Notes**: _____________________________________

## Error Scenario Testing

### Test 4: Invalid File Upload

**Objective**: Verify proper error handling for invalid file uploads

**Test 4a: Non-PDF File**
```bash
echo "This is not a PDF" > test.txt
curl -X POST http://localhost:8000/api/policies/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt"
```

**Expected**:
- Status: 400 Bad Request
- Error message: "Invalid file type. Only PDF files are accepted"

**Test 4b: Corrupted PDF**
```bash
echo "corrupted" > corrupted.pdf
curl -X POST http://localhost:8000/api/policies/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@corrupted.pdf"
```

**Expected**:
- Status: 400 Bad Request or processing fails gracefully
- Policy status marked as "failed"
- Error logged in system

**Test 4c: Oversized File**
```bash
# Create large file (if size limits are configured)
dd if=/dev/zero of=large.pdf bs=1M count=100
curl -X POST http://localhost:8000/api/policies/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large.pdf"
```

**Expected**:
- Status: 413 Payload Too Large (if limit configured)
- Or graceful handling with appropriate error message

**Test Result**: ✅ PASS / ❌ FAIL

### Test 5: Authentication Errors

**Test 5a: Missing Token**
```bash
curl -X GET http://localhost:8000/api/policies
```

**Expected**:
- Status: 401 Unauthorized
- Error message about missing authentication

**Test 5b: Invalid Token**
```bash
curl -X GET http://localhost:8000/api/policies \
  -H "Authorization: Bearer invalid_token_here"
```

**Expected**:
- Status: 401 Unauthorized
- Error message about invalid token

**Test 5c: Expired Token**
```bash
# Use an expired token (wait for expiration or use old token)
curl -X GET http://localhost:8000/api/policies \
  -H "Authorization: Bearer $EXPIRED_TOKEN"
```

**Expected**:
- Status: 401 Unauthorized
- Error message about expired token

**Test Result**: ✅ PASS / ❌ FAIL

### Test 6: Database Connection Failure Recovery

**Objective**: Test system behavior when database is unavailable

**Steps**:

1. Stop PostgreSQL container
   ```bash
   docker-compose stop postgres
   ```

2. Try to access API
   ```bash
   curl -X GET http://localhost:8000/api/policies \
     -H "Authorization: Bearer $TOKEN"
   ```
   
   **Expected**:
   - Status: 503 Service Unavailable
   - Error message about database connection

3. Check health endpoint
   ```bash
   curl http://localhost:8000/health
   ```
   
   **Expected**:
   - Status: 503
   - Database status: "disconnected"

4. Restart PostgreSQL
   ```bash
   docker-compose start postgres
   ```

5. Verify recovery
   ```bash
   curl http://localhost:8000/health
   ```
   
   **Expected**:
   - Status: 200 OK
   - Database status: "connected"
   - System recovers automatically

**Test Result**: ✅ PASS / ❌ FAIL

### Test 7: S3 Connection Failure

**Objective**: Test system behavior when S3 is unavailable

**Steps**:

1. Configure invalid S3 credentials temporarily
2. Try to upload policy
   ```bash
   curl -X POST http://localhost:8000/api/policies/upload \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@sample_data/data_privacy_policy.pdf"
   ```

**Expected**:
- Status: 500 Internal Server Error or 503 Service Unavailable
- Error message about S3 connection failure
- Error logged in backend logs

3. Check health endpoint
   ```bash
   curl http://localhost:8000/health
   ```
   
   **Expected**:
   - S3 status: "disconnected" or "error"

**Test Result**: ✅ PASS / ❌ FAIL

### Test 8: ChromaDB Connection Failure

**Objective**: Test system behavior when ChromaDB is unavailable

**Steps**:

1. Stop ChromaDB container
   ```bash
   docker-compose stop chromadb
   ```

2. Try to perform embedding search
   ```bash
   curl -X POST http://localhost:8000/api/embeddings/search \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query": "data encryption", "top_k": 5}'
   ```

**Expected**:
- Status: 503 Service Unavailable
- Error message about vector database connection

3. Restart ChromaDB
   ```bash
   docker-compose start chromadb
   ```

4. Verify recovery
   ```bash
   curl http://localhost:8000/health
   ```

**Expected**:
- ChromaDB status: "connected"
- System recovers automatically

**Test Result**: ✅ PASS / ❌ FAIL

## API Endpoint Verification

### Test 9: Authentication Endpoints

**POST /api/auth/register**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "organization_name": "New Org"
  }'
```
**Expected**: 200 OK, user created

**POST /api/auth/login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!"
  }'
```
**Expected**: 200 OK, JWT token returned

**GET /api/auth/me**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, user info returned

**Test Result**: ✅ PASS / ❌ FAIL

### Test 10: Policy Endpoints

**POST /api/policies/upload**
```bash
curl -X POST http://localhost:8000/api/policies/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_data/data_privacy_policy.pdf"
```
**Expected**: 200 OK, policy uploaded

**GET /api/policies**
```bash
curl -X GET http://localhost:8000/api/policies \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, list of policies

**GET /api/policies/{policy_id}**
```bash
curl -X GET http://localhost:8000/api/policies/$POLICY_ID \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, policy details

**DELETE /api/policies/{policy_id}**
```bash
curl -X DELETE http://localhost:8000/api/policies/$POLICY_ID \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, policy deleted

**Test Result**: ✅ PASS / ❌ FAIL

### Test 11: Rules Endpoints

**POST /api/rules/extract/{policy_id}**
```bash
curl -X POST http://localhost:8000/api/rules/extract/$POLICY_ID \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, rules extracted

**GET /api/rules**
```bash
curl -X GET http://localhost:8000/api/rules \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, list of rules

**GET /api/rules/{rule_id}**
```bash
curl -X GET http://localhost:8000/api/rules/$RULE_ID \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, rule details

**Test Result**: ✅ PASS / ❌ FAIL

### Test 12: Audit Endpoints

**POST /api/audits/upload**
```bash
curl -X POST http://localhost:8000/api/audits/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_data/violation_document.pdf"
```
**Expected**: 200 OK, audit initiated

**GET /api/audits**
```bash
curl -X GET http://localhost:8000/api/audits \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, list of audits

**GET /api/audits/{audit_id}**
```bash
curl -X GET http://localhost:8000/api/audits/$AUDIT_ID \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, audit summary

**GET /api/audits/{audit_id}/violations**
```bash
curl -X GET http://localhost:8000/api/audits/$AUDIT_ID/violations \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: 200 OK, list of violations

**Test Result**: ✅ PASS / ❌ FAIL

### Test 13: Export Endpoints

**GET /api/exports/csv/{audit_id}**
```bash
curl -X GET http://localhost:8000/api/exports/csv/$AUDIT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -o report.csv
```
**Expected**: 200 OK, CSV file downloaded

**GET /api/exports/pdf/{audit_id}**
```bash
curl -X GET http://localhost:8000/api/exports/pdf/$AUDIT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -o report.pdf
```
**Expected**: 200 OK, PDF file downloaded

**Test Result**: ✅ PASS / ❌ FAIL

### Test 14: Health Check Endpoint

**GET /health**
```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "chromadb": "connected",
    "s3": "connected"
  },
  "timestamp": "2025-02-12T10:00:00Z"
}
```

**Test Result**: ✅ PASS / ❌ FAIL

## Performance Testing

### Test 15: Large Document Processing

**Objective**: Verify system handles large documents efficiently

**Steps**:

1. Upload large policy document (50+ pages)
2. Measure processing time
3. Verify chunking works correctly
4. Check memory usage

**Expected**:
- Processing completes within 5 minutes
- No memory leaks or crashes
- All chunks created successfully
- Embeddings generated for all chunks

**Test Result**: ✅ PASS / ❌ FAIL

**Processing Time**: _______ seconds

### Test 16: Concurrent Uploads

**Objective**: Test system under concurrent load

**Steps**:

1. Upload 5 documents simultaneously
   ```bash
   for i in {1..5}; do
     curl -X POST http://localhost:8000/api/policies/upload \
       -H "Authorization: Bearer $TOKEN" \
       -F "file=@sample_data/data_privacy_policy.pdf" &
   done
   wait
   ```

2. Verify all uploads succeed
3. Check system resources

**Expected**:
- All uploads complete successfully
- No timeouts or errors
- System remains responsive

**Test Result**: ✅ PASS / ❌ FAIL

### Test 17: API Response Times

**Objective**: Verify API endpoints respond within acceptable time limits

**Endpoints to Test**:

| Endpoint | Expected Response Time | Actual Time | Result |
|----------|----------------------|-------------|--------|
| POST /api/auth/login | < 500ms | _____ ms | ✅/❌ |
| GET /api/policies | < 1000ms | _____ ms | ✅/❌ |
| GET /api/rules | < 1000ms | _____ ms | ✅/❌ |
| GET /api/audits | < 1000ms | _____ ms | ✅/❌ |
| GET /health | < 200ms | _____ ms | ✅/❌ |

**Test Result**: ✅ PASS / ❌ FAIL

## Test Results Documentation

### Test Summary

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Complete User Journey | ⬜ | |
| 2 | Compliant Document | ⬜ | |
| 3 | Multi-Tenant Isolation | ⬜ | |
| 4 | Invalid File Upload | ⬜ | |
| 5 | Authentication Errors | ⬜ | |
| 6 | Database Failure Recovery | ⬜ | |
| 7 | S3 Connection Failure | ⬜ | |
| 8 | ChromaDB Failure | ⬜ | |
| 9 | Auth Endpoints | ⬜ | |
| 10 | Policy Endpoints | ⬜ | |
| 11 | Rules Endpoints | ⬜ | |
| 12 | Audit Endpoints | ⬜ | |
| 13 | Export Endpoints | ⬜ | |
| 14 | Health Check | ⬜ | |
| 15 | Large Document | ⬜ | |
| 16 | Concurrent Uploads | ⬜ | |
| 17 | API Response Times | ⬜ | |

**Overall Status**: ⬜ PASS / ⬜ FAIL

**Tests Passed**: _____ / 17

**Tests Failed**: _____

**Date Tested**: _____________________

**Tested By**: _____________________

### Issues Found

| Issue # | Description | Severity | Status |
|---------|-------------|----------|--------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

### Recommendations

1. _____________________________________
2. _____________________________________
3. _____________________________________

## Automated Testing Script

Save this as `run_integration_tests.sh`:

```bash
#!/bin/bash

# AI Compliance Auditor - Automated Integration Tests

set -e

echo "Starting Integration Tests..."
echo "=============================="

# Configuration
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function to run test
run_test() {
    local test_name=$1
    local command=$2
    local expected_status=$3
    
    echo -n "Testing: $test_name... "
    
    response=$(eval $command)
    status=$?
    
    if [ $status -eq $expected_status ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
}

# Test 1: Health Check
run_test "Health Check" \
    "curl -s -o /dev/null -w '%{http_code}' $API_URL/health" \
    200

# Test 2: Register User
run_test "User Registration" \
    "curl -s -o /dev/null -w '%{http_code}' -X POST $API_URL/api/auth/register \
    -H 'Content-Type: application/json' \
    -d '{\"email\":\"test@example.com\",\"password\":\"Pass123!\",\"organization_name\":\"Test Org\"}'" \
    200

# Test 3: Login
TOKEN=$(curl -s -X POST $API_URL/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"test@example.com","password":"Pass123!"}' | jq -r '.access_token')

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo -e "Testing: User Login... ${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "Testing: User Login... ${RED}FAIL${NC}"
    ((FAILED++))
fi

# Summary
echo ""
echo "=============================="
echo "Test Summary"
echo "=============================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
```

Make executable:
```bash
chmod +x run_integration_tests.sh
./run_integration_tests.sh
```

## Continuous Integration

Add to `.github/workflows/integration-tests.yml`:

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run integration tests
        run: ./run_integration_tests.sh
      
      - name: Stop services
        run: docker-compose down
```

## Next Steps

After completing integration testing:

1. Document all issues found
2. Create tickets for bug fixes
3. Implement fixes and re-test
4. Update documentation based on findings
5. Prepare for production deployment

## Support

For testing support:
- Review logs: `docker-compose logs -f`
- Check health: `curl http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
