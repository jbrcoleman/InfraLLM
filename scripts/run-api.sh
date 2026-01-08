#!/bin/bash
# Start the InfraLLM API server

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting InfraLLM API Server...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. API may not work correctly."
    echo "Run 'infrallm configure' to set up your environment."
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install fastapi "uvicorn[standard]"
fi

echo -e "${GREEN}Starting server on http://localhost:8000${NC}"
echo -e "${GREEN}API docs available at http://localhost:8000/docs${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn infrallm_api.main:app --host 0.0.0.0 --port 8000 --reload
