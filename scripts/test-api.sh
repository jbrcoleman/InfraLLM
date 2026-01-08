#!/bin/bash
# Test the InfraLLM API

set -e

API_URL=${API_URL:-http://localhost:8000}

echo "Testing InfraLLM API at $API_URL"
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s "$API_URL/api/v1/health" | python -m json.tool
echo ""

# Test root endpoint
echo "2. Testing root endpoint..."
curl -s "$API_URL/" | python -m json.tool
echo ""

# Test dry-run endpoint (only if configured)
if [ -f ".env" ]; then
    echo "3. Testing dry-run endpoint..."
    curl -s -X POST "$API_URL/api/v1/dry-run" \
        -H "Content-Type: application/json" \
        -d '{"request": "dev S3 bucket for testing"}' \
        | python -m json.tool || echo "Dry-run test skipped (requires valid API keys)"
    echo ""
fi

echo "API tests complete!"
echo "Visit $API_URL/docs for interactive API documentation"
