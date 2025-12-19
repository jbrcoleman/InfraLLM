"""
InfraLLM FastAPI Application.

REST API wrapper for InfraLLM core functionality.
"""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .models.requests import (
    ProvisionRequest,
    ProvisionResponse,
    DryRunRequest,
    DryRunResponse,
    RequestStatus,
    StatusResponse,
    HealthResponse,
)
from .store import request_store
from .worker import process_provision_request
from . import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting InfraLLM API service")
    yield
    logger.info("Shutting down InfraLLM API service")


# Create FastAPI app
app = FastAPI(
    title="InfraLLM API",
    description="AI-powered infrastructure provisioning API for Backstage integration",
    version=__version__,
    lifespan=lifespan,
)

# CORS middleware for Backstage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "InfraLLM API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns service health status and component checks.
    """
    checks = {"api": "healthy"}

    # Check Claude API configuration
    try:
        from src.llm.client import ClaudeClient
        ClaudeClient()  # Just verify it can be instantiated
        checks["claude"] = "connected"
    except Exception as e:
        logger.warning(f"Claude API check failed: {str(e)}")
        checks["claude"] = f"error: {str(e)}"

    # Check GitHub configuration
    try:
        from src.git.github import GitHubClient
        GitHubClient()  # Just verify it can be instantiated
        checks["github"] = "connected"
    except Exception as e:
        logger.warning(f"GitHub API check failed: {str(e)}")
        checks["github"] = f"error: {str(e)}"

    # Determine overall status
    status = "healthy" if all(v == "healthy" or v == "connected" for v in checks.values()) else "degraded"

    return HealthResponse(
        status=status,
        version=__version__,
        checks=checks,
    )


@app.post("/api/v1/provision", response_model=ProvisionResponse, tags=["provision"])
async def provision_infrastructure(
    request: ProvisionRequest,
    background_tasks: BackgroundTasks,
):
    """
    Provision infrastructure from natural language request.

    This endpoint:
    - Accepts a natural language infrastructure request
    - Queues the request for processing
    - Returns immediately with a request ID
    - Processes in background: parses with Claude, generates Terraform, creates PR

    Use the `/api/v1/requests/{request_id}/status` endpoint to poll for completion.
    """
    # Generate unique request ID
    request_id = f"req-{uuid.uuid4().hex[:12]}"

    logger.info(
        f"Received provision request {request_id} from {request.requester}: {request.request}"
    )

    # Store request
    request_store.create(
        request_id=request_id,
        request_text=request.request,
        requester=request.requester,
        team=request.team,
        service=request.service,
    )

    # Process in background
    background_tasks.add_task(
        process_provision_request,
        request_id=request_id,
        request_text=request.request,
        requester=request.requester,
        environment=request.environment,
    )

    return ProvisionResponse(
        request_id=request_id,
        status=RequestStatus.QUEUED,
        message="Request queued for processing",
    )


@app.get("/api/v1/requests/{request_id}/status", response_model=StatusResponse, tags=["status"])
async def get_request_status(request_id: str):
    """
    Get status of a provision request.

    Returns detailed information about the request including:
    - Current status (queued, parsing, generating, creating_pr, completed, failed)
    - PR URL when completed
    - Error message if failed
    - Timestamps
    """
    status_response = request_store.get_status_response(request_id)

    if status_response is None:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

    return status_response


@app.get("/api/v1/requests", tags=["status"])
async def list_requests(
    user: str = Query(..., description="Filter by user email"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
):
    """
    List provision requests for a user.

    Returns a list of requests filtered by user, sorted by creation time (newest first).
    """
    requests = request_store.list_by_user(user, limit=limit)

    return {
        "requests": requests,
        "count": len(requests),
        "user": user,
    }


@app.post("/api/v1/dry-run", response_model=DryRunResponse, tags=["dry-run"])
async def dry_run(request: DryRunRequest):
    """
    Preview generated Terraform code without creating a PR.

    This endpoint:
    - Parses the request with Claude
    - Generates Terraform code
    - Returns the parsed requirements and generated files
    - Does NOT create any GitHub PR

    Use this for testing and previewing before actual provisioning.
    """
    from src.llm.client import ClaudeClient
    from src.llm.exceptions import (
        ConfigurationError,
        APIError,
        ValidationError as PolicyValidationError,
        ParsingError,
    )
    from src.terraform.generator import TerraformGenerator
    from src.terraform.exceptions import TerraformGenerationError

    try:
        logger.info(f"Dry-run request: {request.request}")

        # Parse with Claude
        claude_client = ClaudeClient()
        requirements = claude_client.parse_infrastructure_request(request.request)

        # Generate Terraform
        generator = TerraformGenerator()
        terraform = generator.generate(requirements)

        return DryRunResponse(
            parsed_requirements=requirements,
            terraform_files=terraform.files,
            directory=terraform.get_directory_name(),
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

    except PolicyValidationError as e:
        logger.error(f"Policy validation failed: {str(e)}")
        violations_str = "; ".join(e.violations) if hasattr(e, "violations") else str(e)
        raise HTTPException(status_code=400, detail=f"Policy validation failed: {violations_str}")

    except ParsingError as e:
        logger.error(f"Parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse request: {str(e)}")

    except TerraformGenerationError as e:
        logger.error(f"Terraform generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Terraform: {str(e)}")

    except APIError as e:
        logger.error(f"API error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"External API error: {str(e)}")

    except Exception as e:
        logger.exception("Unexpected error in dry-run")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
