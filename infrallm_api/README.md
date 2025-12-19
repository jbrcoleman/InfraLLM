# InfraLLM API Service

FastAPI wrapper around InfraLLM core for Backstage integration and web access.

## Overview

The InfraLLM API Service provides a REST API interface for InfraLLM's infrastructure provisioning capabilities. It's designed to integrate with Backstage and other developer portals while maintaining compatibility with the existing CLI tool.

## Features

- **Async Processing**: Non-blocking provision requests with background task processing
- **Status Tracking**: Real-time status updates for provision requests
- **Dry-Run Mode**: Preview Terraform code before creating PRs
- **Health Checks**: Built-in health monitoring endpoints
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`

## Quick Start

### Running Locally

1. **Install dependencies**:
```bash
pip install fastapi "uvicorn[standard]"
```

2. **Set up environment variables** (same as CLI):
```bash
# Copy from existing .env or create new one
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
export GITHUB_ORG=your-org
export GITHUB_REPO=infrastructure
```

3. **Run the API server**:
```bash
# From project root
uvicorn infrallm_api.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access the API**:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### Running with Docker

1. **Build the Docker image**:
```bash
docker build -f Dockerfile.api -t infrallm-api:latest .
```

2. **Run with Docker Compose**:
```bash
docker-compose -f docker-compose.api.yml up -d
```

3. **Check logs**:
```bash
docker-compose -f docker-compose.api.yml logs -f
```

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

Returns service health status and component checks.

**Example Response**:
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "checks": {
    "api": "healthy",
    "claude": "connected",
    "github": "connected"
  }
}
```

### Provision Infrastructure
```bash
POST /api/v1/provision
```

Queue an infrastructure provision request.

**Request Body**:
```json
{
  "request": "production Postgres database for payments API",
  "requester": "user@company.com",
  "team": "payments-team",
  "service": "payments-api",
  "environment": "prod"
}
```

**Response**:
```json
{
  "request_id": "req-a1b2c3d4e5f6",
  "status": "queued",
  "message": "Request queued for processing"
}
```

### Get Request Status
```bash
GET /api/v1/requests/{request_id}/status
```

Get detailed status of a provision request.

**Example Response**:
```json
{
  "request_id": "req-a1b2c3d4e5f6",
  "request_text": "production Postgres database for payments API",
  "requester": "user@company.com",
  "team": "payments-team",
  "status": "completed",
  "pr_url": "https://github.com/org/infrastructure/pull/123",
  "pr_number": 123,
  "branch_name": "infrallm/prod-postgres-payments-api",
  "created_at": "2025-12-19T10:00:00Z",
  "completed_at": "2025-12-19T10:00:15Z"
}
```

**Status Values**:
- `queued`: Request received, waiting to process
- `parsing`: Parsing request with Claude AI
- `generating`: Generating Terraform code
- `creating_pr`: Creating GitHub pull request
- `completed`: PR created successfully
- `failed`: Error occurred (check `error` field)

### List User Requests
```bash
GET /api/v1/requests?user=user@company.com&limit=20
```

List recent requests for a user.

### Dry Run (Preview)
```bash
POST /api/v1/dry-run
```

Preview generated Terraform without creating a PR.

**Request Body**:
```json
{
  "request": "staging S3 bucket for logs"
}
```

**Response**:
```json
{
  "parsed_requirements": {
    "resource_type": "s3",
    "resource_name": "logs-bucket",
    "environment": "staging",
    ...
  },
  "terraform_files": {
    "main.tf": "resource \"aws_s3_bucket\" ...",
    "variables.tf": "variable ...",
    "outputs.tf": "output ..."
  },
  "directory": "terraform/staging/s3/logs-bucket"
}
```

## Usage Examples

### Using curl

**Provision infrastructure**:
```bash
curl -X POST http://localhost:8000/api/v1/provision \
  -H "Content-Type: application/json" \
  -d '{
    "request": "production RDS Postgres for user service",
    "requester": "developer@company.com",
    "team": "backend-team"
  }'
```

**Check status**:
```bash
REQUEST_ID="req-a1b2c3d4e5f6"
curl http://localhost:8000/api/v1/requests/$REQUEST_ID/status
```

**Dry run**:
```bash
curl -X POST http://localhost:8000/api/v1/dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "request": "staging S3 bucket for logs"
  }'
```

### Using Python

```python
import requests

# Provision infrastructure
response = requests.post(
    "http://localhost:8000/api/v1/provision",
    json={
        "request": "production Postgres for payments API",
        "requester": "user@company.com",
        "team": "payments-team"
    }
)
request_id = response.json()["request_id"]

# Poll for completion
import time
while True:
    status = requests.get(
        f"http://localhost:8000/api/v1/requests/{request_id}/status"
    ).json()

    print(f"Status: {status['status']}")

    if status["status"] in ["completed", "failed"]:
        if status["status"] == "completed":
            print(f"PR created: {status['pr_url']}")
        else:
            print(f"Error: {status['error']}")
        break

    time.sleep(2)
```

### Using JavaScript (Backstage)

```typescript
// Provision infrastructure
const response = await fetch('http://infrallm-api:8000/api/v1/provision', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    request: 'production Postgres for user service',
    requester: user.email,
    team: 'backend-team',
  }),
});

const { request_id } = await response.json();

// Poll for status
const checkStatus = async () => {
  const statusRes = await fetch(
    `http://infrallm-api:8000/api/v1/requests/${request_id}/status`
  );
  const status = await statusRes.json();

  if (status.status === 'completed') {
    console.log('PR created:', status.pr_url);
  } else if (status.status === 'failed') {
    console.error('Error:', status.error);
  } else {
    // Still processing, check again
    setTimeout(checkStatus, 2000);
  }
};

checkStatus();
```

## Configuration

The API service uses the same configuration as the CLI tool:

**Environment Variables**:
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `GITHUB_TOKEN`: GitHub personal access token (required)
- `GITHUB_ORG`: GitHub organization or username (required)
- `GITHUB_REPO`: GitHub repository name (required)
- `DEFAULT_ENVIRONMENT`: Default environment (default: "dev")

**Configuration File**: `.env` in project root

## Production Deployment

### Kubernetes

See [docs/backstage-integration-plan.md](../docs/backstage-integration-plan.md) for Kubernetes deployment examples.

### Important Production Considerations

1. **Replace In-Memory Store**:
   - Current implementation uses in-memory request storage
   - For production, replace with Redis or PostgreSQL
   - See `infrallm_api/store.py`

2. **CORS Configuration**:
   - Update CORS settings in `main.py` for your domain
   - Currently allows all origins (`allow_origins=["*"]`)

3. **Rate Limiting**:
   - Add rate limiting middleware (e.g., slowapi)
   - Prevent API abuse

4. **Authentication**:
   - Integrate with your auth system
   - Verify requester identity
   - Use Backstage JWT tokens

5. **Monitoring**:
   - Add Prometheus metrics
   - Log to centralized logging system
   - Set up alerts for failures

6. **Scaling**:
   - Run multiple API instances behind load balancer
   - Use Redis for distributed request queue
   - Consider async task queue (Celery, RQ)

## Development

### Running Tests

```bash
pytest infrallm_api/
```

### Code Formatting

```bash
black infrallm_api/
ruff check infrallm_api/
```

### Development Server with Auto-Reload

```bash
uvicorn infrallm_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Backstage / Client              │
└──────────────┬──────────────────────────┘
               │ HTTP REST API
               ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌───────────────────────────────────┐  │
│  │  Endpoints                        │  │
│  │  - POST /provision                │  │
│  │  - GET  /requests/{id}/status     │  │
│  │  - POST /dry-run                  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Background Tasks                 │  │
│  │  - Parse with Claude              │  │
│  │  - Generate Terraform             │  │
│  │  - Create GitHub PR               │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Request Store                    │  │
│  │  (In-memory / Redis / PostgreSQL) │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │ Uses
               ▼
┌─────────────────────────────────────────┐
│         InfraLLM Core                   │
│  - ClaudeClient                         │
│  - TerraformGenerator                   │
│  - GitHubClient                         │
└─────────────────────────────────────────┘
```

## Troubleshooting

### API won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies:
```bash
pip install fastapi "uvicorn[standard]"
```

### Health check fails

**Error**: Claude or GitHub check shows error

**Solution**: Verify environment variables:
```bash
echo $ANTHROPIC_API_KEY
echo $GITHUB_TOKEN
```

### Request stays in "queued" status

**Issue**: Background task not processing

**Solution**:
- Check API logs for errors
- Verify Claude API key is valid
- Ensure GitHub token has correct permissions

## License

Same as InfraLLM core.

## Support

For issues and questions:
- GitHub Issues: [your-org/infrallm/issues](https://github.com/your-org/infrallm/issues)
- Documentation: [docs/](../docs/)
