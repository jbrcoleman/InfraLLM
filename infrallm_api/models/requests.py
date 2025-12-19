"""
Request and response models for the InfraLLM API.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RequestStatus(str, Enum):
    """Status of a provision request."""
    QUEUED = "queued"
    PARSING = "parsing"
    GENERATING = "generating"
    CREATING_PR = "creating_pr"
    COMPLETED = "completed"
    FAILED = "failed"


class ProvisionRequest(BaseModel):
    """Request to provision infrastructure."""
    request: str = Field(..., description="Natural language infrastructure request")
    requester: str = Field(..., description="Email or username of requester")
    team: Optional[str] = Field(None, description="Team name for tagging")
    service: Optional[str] = Field(None, description="Service to link infrastructure to")
    environment: Optional[str] = Field(None, description="Environment override (dev/staging/prod)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request": "production Postgres database for payments API",
                    "requester": "user@company.com",
                    "team": "payments-team"
                }
            ]
        }
    }


class ProvisionResponse(BaseModel):
    """Response from provision request."""
    request_id: str = Field(..., description="Unique request identifier")
    status: RequestStatus = Field(..., description="Current status of request")
    pr_url: Optional[str] = Field(None, description="GitHub PR URL when completed")
    message: Optional[str] = Field(None, description="Status message or error")


class DryRunRequest(BaseModel):
    """Request for dry-run (preview) mode."""
    request: str = Field(..., description="Natural language infrastructure request")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request": "staging S3 bucket for logs with 90-day lifecycle"
                }
            ]
        }
    }


class DryRunResponse(BaseModel):
    """Response from dry-run request."""
    parsed_requirements: Dict[str, Any] = Field(..., description="Parsed infrastructure requirements")
    terraform_files: Dict[str, str] = Field(..., description="Generated Terraform files")
    directory: str = Field(..., description="Target directory path")


class StatusResponse(BaseModel):
    """Detailed status of a provision request."""
    request_id: str = Field(..., description="Request identifier")
    request_text: str = Field(..., description="Original request text")
    requester: str = Field(..., description="User who made the request")
    team: Optional[str] = Field(None, description="Team name")
    service: Optional[str] = Field(None, description="Linked service")
    status: RequestStatus = Field(..., description="Current status")
    pr_url: Optional[str] = Field(None, description="GitHub PR URL")
    pr_number: Optional[int] = Field(None, description="GitHub PR number")
    branch_name: Optional[str] = Field(None, description="Git branch name")
    error: Optional[str] = Field(None, description="Error message if failed")
    requirements: Optional[Dict[str, Any]] = Field(None, description="Parsed requirements")
    created_at: datetime = Field(..., description="Request creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Request completion timestamp")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    checks: Dict[str, str] = Field(..., description="Component health checks")
