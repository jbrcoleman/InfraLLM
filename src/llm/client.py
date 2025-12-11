"""
Claude API client for parsing natural language infrastructure requests.

This module integrates with the Anthropic Claude API to parse natural language
infrastructure requests into structured JSON format with policy validation.
"""

import os
import json
import logging
from typing import Dict, Any

import anthropic
from pydantic import ValidationError as PydanticValidationError

from src.llm.exceptions import (
    ConfigurationError,
    APIError,
    ValidationError,
    ParsingError
)
from src.llm.models import InfrastructureRequest
from src.llm.prompts import build_system_prompt
from src.llm.validator import validate_request
from src.config.loader import load_policies


# Set up logging
logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Client for interacting with Claude API to parse infrastructure requests.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.

        Raises:
            ConfigurationError: If API key is not provided and not in environment
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY must be provided or set in environment.\n"
                "Set it in your .env file or export it as an environment variable."
            )

    def parse_infrastructure_request(self, request: str) -> Dict[str, Any]:
        """
        Parse natural language infrastructure request into structured format.

        This method orchestrates the entire parsing workflow:
        1. Pre-flight validation
        2. Load organizational policies
        3. Build system prompt
        4. Call Claude API
        5. Parse JSON response
        6. Validate with Pydantic
        7. Validate against policies
        8. Return structured data

        Args:
            request: Natural language description of infrastructure needs

        Returns:
            Dictionary containing:
                - resource_type: Type of resource (rds, s3, eks, etc.)
                - resource_name: Name following naming convention
                - parameters: Resource-specific parameters
                - environment: Target environment (dev, staging, prod)
                - tags: Required organizational tags

        Raises:
            ConfigurationError: If API key missing or policies invalid
            APIError: If Claude API call fails
            ParsingError: If response cannot be parsed as valid JSON
            ValidationError: If request violates organizational policies

        Example:
            >>> client = ClaudeClient()
            >>> result = client.parse_infrastructure_request(
            ...     "I need a production Postgres database for payments API with 200GB storage"
            ... )
            >>> print(result['resource_type'])
            'rds'
            >>> print(result['resource_name'])
            'prod-payments-db'
        """
        # Step 1: Pre-flight validation
        if not request or not request.strip():
            raise ValidationError(["Infrastructure request cannot be empty"])

        logger.info(f"Parsing infrastructure request: {request[:100]}...")

        # Step 2: Load organizational policies
        try:
            policies = load_policies()
        except ConfigurationError as e:
            logger.error(f"Failed to load policies: {e}")
            raise

        # Step 3: Build system prompt with policies
        system_prompt = build_system_prompt(policies)
        logger.debug(f"System prompt length: {len(system_prompt)} characters")

        # Step 4: Call Claude API
        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            logger.debug("Calling Claude API...")
            response = client.messages.create(
                model="claude-sonnet-4-5",  # Using Claude Sonnet 4.5 (most capable)
                max_tokens=4096,
                temperature=0,  # Deterministic output
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": request
                    }
                ]
            )

            # Extract text from response
            raw_response = response.content[0].text
            logger.debug(f"Claude response: {raw_response[:200]}...")

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise APIError(
                f"Failed to call Claude API: {str(e)}\n"
                "Please check your API key and network connection."
            )
        except Exception as e:
            logger.error(f"Unexpected error calling Claude API: {e}")
            raise APIError(f"Unexpected error calling Claude API: {str(e)}")

        # Step 5: Parse JSON response
        try:
            # Strip markdown code blocks if present (e.g., ```json ... ```)
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```"):
                # Remove opening ```json or ```
                lines = cleaned_response.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_response = '\n'.join(lines)

            parsed_data = json.loads(cleaned_response)
            logger.debug(f"Successfully parsed JSON response")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from Claude: {e}")
            logger.error(f"Raw response: {raw_response}")
            raise ParsingError(
                f"Claude returned invalid JSON: {str(e)}\n"
                f"Raw response: {raw_response[:500]}"
            )

        # Step 6: Validate with Pydantic model
        try:
            validated_request = InfrastructureRequest(**parsed_data)
            logger.info(
                f"Validated request: {validated_request.resource_type} "
                f"'{validated_request.resource_name}' in {validated_request.environment}"
            )
        except PydanticValidationError as e:
            logger.error(f"Pydantic validation failed: {e}")
            raise ParsingError(
                f"Claude response does not match expected schema:\n{str(e)}"
            )

        # Step 7: Validate against organizational policies
        policy_violations = validate_request(validated_request, policies)

        if policy_violations:
            logger.warning(f"Policy violations found: {policy_violations}")
            raise ValidationError(policy_violations)

        logger.info("Request successfully parsed and validated")

        # Step 8: Return as dictionary
        return validated_request.model_dump()
