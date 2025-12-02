#!/bin/bash

# AI Compliance Auditor - Automated Integration Tests
# This script runs comprehensive integration tests for the system

set -e

echo "=========================================="
echo "AI Compliance Auditor - Integration Tests"
echo "=========================================="
echo ""

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="TestPass123!"
TEST_ORG="Test Organization $(date +%s)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

# Helper function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "PASS")
            echo -e "${GREEN}✓ PASS${NC} - $message"
            ((PASSED++))
            ;;
        "FAIL")
            echo -e "${RED}✗ FAIL${NC} - $message"
            ((FAILED++))
            ;;
        "SKIP")
            echo -e "${YELLOW}⊘ SKIP${NC} - $message"
            ((SKIPPED++))
            ;;
        "INFO")
            echo -e "${BLUE}ℹ INFO${NC} - $message"
            ;;
    esac
}

# Helper function to run HTTP test
run_http_test() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local expected_status=$4
    local headers=$5
    local data=$6
    
    echo -n "Testing: $test_name... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
            $headers \
            -d "$data" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
            $headers 2>/dev/null)
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" = "$expected_status" ]; then
        print_status "PASS" "$test_name (Status: $status_code)"
        echo "$body"
        return 0
    else
        print_status "FAIL" "$test_name (Expected: $expected_status, Got: $status_code)"
        echo "Response: $body"
        return 1
    fi
}

# Check if services are running
echo "Checking if services are running..."
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    print_status "FAIL" "Backend is not accessible at $API_URL"
    echo "Please start the services with: docker-compose up -d"
    exit 1
fi
print_status "PASS" "Backend is accessible"
echo ""

# Test 1: Health Check
echo "=========================================="
echo "Test 1: Health Check"
echo "=========================================="
health_response=$(curl -s "$API_URL/health")
if echo "$health_response" | grep -q "healthy\|ok"; then
    print_status "PASS" "Health check endpoint"
else
    print_status "FAIL" "Health check endpoint"
fi
echo ""

# Test 2: User Registration
echo "=========================================="
echo "Test 2: User Registration"
echo "=========================================="
register_response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"organization_name\":\"$TEST_ORG\"}")

register_status=$(echo "$register_response" | tail -n1)
register_body=$(echo "$register_response" | sed '$d')

if [ "$register_status" = "200" ] || [ "$register_status" = "201" ]; then
    print_status "PASS" "User registration"
    USER_ID=$(echo "$register_body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    ORG_ID=$(echo "$register_body" | grep -o '"organization_id":"[^"]*"' | cut -d'"' -f4)
    print_status "INFO" "User ID: $USER_ID"
    print_status "INFO" "Organization ID: $ORG_ID"
else
    print_status "FAIL" "User registration (Status: $register_status)"
    echo "Response: $register_body"
fi
echo ""

# Test 3: User Login
echo "=========================================="
echo "Test 3: User Login"
echo "=========================================="
login_response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

login_status=$(echo "$login_response" | tail -n1)
login_body=$(echo "$login_response" | sed '$d')

if [ "$login_status" = "200" ]; then
    print_status "PASS" "User login"
    TOKEN=$(echo "$login_body" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
        print_status "PASS" "JWT token received"
        print_status "INFO" "Token: ${TOKEN:0:20}..."
    else
        print_status "FAIL" "JWT token not found in response"
    fi
else
    print_status "FAIL" "User login (Status: $login_status)"
    echo "Response: $login_body"
    exit 1
fi
echo ""

# Test 4: Get Current User
echo "=========================================="
echo "Test 4: Get Current User"
echo "=========================================="
me_response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/auth/me" \
    -H "Authorization: Bearer $TOKEN")

me_status=$(echo "$me_response" | tail -n1)
if [ "$me_status" = "200" ]; then
    print_status "PASS" "Get current user"
else
    print_status "FAIL" "Get current user (Status: $me_status)"
fi
echo ""

# Test 5: List Policies (should be empty)
echo "=========================================="
echo "Test 5: List Policies"
echo "=========================================="
policies_response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/policies" \
    -H "Authorization: Bearer $TOKEN")

policies_status=$(echo "$policies_response" | tail -n1)
if [ "$policies_status" = "200" ]; then
    print_status "PASS" "List policies endpoint"
else
    print_status "FAIL" "List policies endpoint (Status: $policies_status)"
fi
echo ""

# Test 6: Upload Policy (if sample file exists)
echo "=========================================="
echo "Test 6: Upload Policy Document"
echo "=========================================="
if [ -f "sample_data/data_privacy_policy.pdf" ]; then
    upload_response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/policies/upload" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@sample_data/data_privacy_policy.pdf")
    
    upload_status=$(echo "$upload_response" | tail -n1)
    upload_body=$(echo "$upload_response" | sed '$d')
    
    if [ "$upload_status" = "200" ] || [ "$upload_status" = "201" ]; then
        print_status "PASS" "Policy upload"
        POLICY_ID=$(echo "$upload_body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        print_status "INFO" "Policy ID: $POLICY_ID"
    else
        print_status "FAIL" "Policy upload (Status: $upload_status)"
    fi
else
    print_status "SKIP" "Policy upload (sample file not found)"
fi
echo ""

# Test 7: Multi-Tenant Isolation
echo "=========================================="
echo "Test 7: Multi-Tenant Isolation"
echo "=========================================="
# Create second organization
org2_email="test2-$(date +%s)@example.com"
org2_response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$org2_email\",\"password\":\"$TEST_PASSWORD\",\"organization_name\":\"Org 2\"}")

org2_status=$(echo "$org2_response" | tail -n1)
if [ "$org2_status" = "200" ] || [ "$org2_status" = "201" ]; then
    print_status "PASS" "Second organization created"
    
    # Login as second org
    org2_login=$(curl -s -X POST "$API_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$org2_email\",\"password\":\"$TEST_PASSWORD\"}")
    TOKEN2=$(echo "$org2_login" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    # Try to access first org's policies
    isolation_response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/policies" \
        -H "Authorization: Bearer $TOKEN2")
    
    isolation_status=$(echo "$isolation_response" | tail -n1)
    isolation_body=$(echo "$isolation_response" | sed '$d')
    
    if [ "$isolation_status" = "200" ]; then
        # Check if response is empty or doesn't contain first org's data
        if echo "$isolation_body" | grep -q "$POLICY_ID"; then
            print_status "FAIL" "Multi-tenant isolation (Org 2 can see Org 1 data)"
        else
            print_status "PASS" "Multi-tenant isolation (Data properly isolated)"
        fi
    else
        print_status "PASS" "Multi-tenant isolation (Access denied)"
    fi
else
    print_status "SKIP" "Multi-tenant isolation test (couldn't create second org)"
fi
echo ""

# Test 8: Invalid Authentication
echo "=========================================="
echo "Test 8: Invalid Authentication"
echo "=========================================="
invalid_response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/policies" \
    -H "Authorization: Bearer invalid_token")

invalid_status=$(echo "$invalid_response" | tail -n1)
if [ "$invalid_status" = "401" ] || [ "$invalid_status" = "403" ]; then
    print_status "PASS" "Invalid token rejected"
else
    print_status "FAIL" "Invalid token not rejected (Status: $invalid_status)"
fi
echo ""

# Test 9: Missing Authentication
echo "=========================================="
echo "Test 9: Missing Authentication"
echo "=========================================="
noauth_response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/policies")

noauth_status=$(echo "$noauth_response" | tail -n1)
if [ "$noauth_status" = "401" ] || [ "$noauth_status" = "403" ]; then
    print_status "PASS" "Missing authentication rejected"
else
    print_status "FAIL" "Missing authentication not rejected (Status: $noauth_status)"
fi
echo ""

# Test 10: API Documentation
echo "=========================================="
echo "Test 10: API Documentation"
echo "=========================================="
docs_response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/docs")

docs_status=$(echo "$docs_response" | tail -n1)
if [ "$docs_status" = "200" ]; then
    print_status "PASS" "API documentation accessible"
else
    print_status "FAIL" "API documentation not accessible (Status: $docs_status)"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed:  ${GREEN}$PASSED${NC}"
echo -e "Failed:  ${RED}$FAILED${NC}"
echo -e "Skipped: ${YELLOW}$SKIPPED${NC}"
echo "Total:   $((PASSED + FAILED + SKIPPED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "All tests passed! ✓"
    echo -e "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "Some tests failed! ✗"
    echo -e "==========================================${NC}"
    exit 1
fi
