#!/bin/bash
# InfraLLM Phase 2 Test Commands
# Run these after setting your ANTHROPIC_API_KEY

echo "=========================================="
echo "InfraLLM Phase 2 Test Suite"
echo "=========================================="
echo ""

# Load environment variables
set -a
source .env
set +a

# Verify API key is set
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY not set or still using placeholder"
    echo ""
    echo "Please update your .env file with a real API key:"
    echo "  1. Get your key from https://console.anthropic.com/"
    echo "  2. Edit .env file: nano .env"
    echo "  3. Replace 'your_anthropic_api_key_here' with your actual key"
    echo ""
    exit 1
fi

echo "✓ API key configured"
echo ""

# Test 1: Production RDS database
echo "----------------------------------------"
echo "Test 1: Production RDS Database"
echo "----------------------------------------"
python -m src.main dry-run "I need a production Postgres database for the payments API with 200GB storage and daily backups"
echo ""

# Test 2: Staging S3 bucket
echo "----------------------------------------"
echo "Test 2: Staging S3 Bucket"
echo "----------------------------------------"
python -m src.main dry-run "Create a staging S3 bucket for log aggregation with 90-day lifecycle policy"
echo ""

# Test 3: Production EKS cluster
echo "----------------------------------------"
echo "Test 3: Production EKS Cluster"
echo "----------------------------------------"
python -m src.main dry-run "Set up a production Kubernetes cluster for the API service with 5 nodes"
echo ""

# Test 4: Verbose mode
echo "----------------------------------------"
echo "Test 4: Verbose Mode (full JSON)"
echo "----------------------------------------"
python -m src.main provision "dev MySQL database for testing" --verbose
echo ""

# Test 5: Ambiguous request (should use defaults)
echo "----------------------------------------"
echo "Test 5: Ambiguous Request (tests defaults)"
echo "----------------------------------------"
python -m src.main dry-run "I need a database"
echo ""

echo "=========================================="
echo "Test suite complete!"
echo "=========================================="
