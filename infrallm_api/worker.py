"""
Background worker for processing provision requests.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from src.llm.client import ClaudeClient
from src.llm.exceptions import (
    ConfigurationError,
    APIError,
    ValidationError as PolicyValidationError,
    ParsingError,
)
from src.terraform.generator import TerraformGenerator
from src.terraform.exceptions import TerraformGenerationError
from src.git.github import GitHubClient
from src.git.exceptions import GitHubError

from .models.requests import RequestStatus
from .store import request_store

logger = logging.getLogger(__name__)


async def process_provision_request(
    request_id: str,
    request_text: str,
    requester: str,
    environment: str = None,
) -> None:
    """
    Background task to process a provision request.

    This function:
    1. Parses the request with Claude
    2. Generates Terraform code
    3. Creates a GitHub PR
    4. Updates the request status throughout
    """
    try:
        # Update status: parsing
        logger.info(f"Starting provision request {request_id}")
        request_store.update(request_id, status=RequestStatus.PARSING)

        # Parse with Claude
        logger.info(f"Parsing request {request_id} with Claude")
        claude_client = ClaudeClient()
        requirements = claude_client.parse_infrastructure_request(request_text)

        # Override environment if provided
        if environment:
            requirements["environment"] = environment

        # Update status: generating
        request_store.update(
            request_id,
            status=RequestStatus.GENERATING,
            requirements=requirements,
        )

        # Generate Terraform
        logger.info(f"Generating Terraform for request {request_id}")
        generator = TerraformGenerator()
        terraform = generator.generate(requirements)

        # Update status: creating PR
        request_store.update(request_id, status=RequestStatus.CREATING_PR)

        # Create GitHub PR
        logger.info(f"Creating GitHub PR for request {request_id}")
        github_client = GitHubClient()
        pr_result = github_client.create_pr(terraform, requirements)

        # Update with results: completed
        logger.info(f"Request {request_id} completed successfully")
        request_store.update(
            request_id,
            status=RequestStatus.COMPLETED,
            pr_url=pr_result["pr_url"],
            pr_number=pr_result["pr_number"],
            branch_name=pr_result["branch_name"],
            completed_at=datetime.utcnow(),
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error for request {request_id}: {str(e)}")
        request_store.update(
            request_id,
            status=RequestStatus.FAILED,
            error=f"Configuration error: {str(e)}",
            completed_at=datetime.utcnow(),
        )

    except PolicyValidationError as e:
        logger.error(f"Policy validation failed for request {request_id}: {str(e)}")
        violations_str = "; ".join(e.violations) if hasattr(e, "violations") else str(e)
        request_store.update(
            request_id,
            status=RequestStatus.FAILED,
            error=f"Policy validation failed: {violations_str}",
            completed_at=datetime.utcnow(),
        )

    except ParsingError as e:
        logger.error(f"Parsing error for request {request_id}: {str(e)}")
        request_store.update(
            request_id,
            status=RequestStatus.FAILED,
            error=f"Failed to parse request: {str(e)}",
            completed_at=datetime.utcnow(),
        )

    except TerraformGenerationError as e:
        logger.error(f"Terraform generation error for request {request_id}: {str(e)}")
        request_store.update(
            request_id,
            status=RequestStatus.FAILED,
            error=f"Failed to generate Terraform: {str(e)}",
            completed_at=datetime.utcnow(),
        )

    except (GitHubError, Exception) as e:
        logger.error(f"GitHub error for request {request_id}: {str(e)}")
        request_store.update(
            request_id,
            status=RequestStatus.FAILED,
            error=f"GitHub error: {str(e)}",
            completed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.exception(f"Unexpected error for request {request_id}")
        request_store.update(
            request_id,
            status=RequestStatus.FAILED,
            error=f"Unexpected error: {str(e)}",
            completed_at=datetime.utcnow(),
        )
