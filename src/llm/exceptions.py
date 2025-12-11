"""
Custom exceptions for InfraLLM.

This module defines the exception hierarchy used throughout the application
for clear error handling and user-friendly error messages.
"""

from typing import List


class InfraLLMError(Exception):
    """Base exception for all InfraLLM errors."""
    pass


class ConfigurationError(InfraLLMError):
    """
    Raised when there are configuration issues.

    Examples:
        - Missing API key
        - Invalid policies.yaml
        - Missing required environment variables
    """
    pass


class APIError(InfraLLMError):
    """
    Raised when Claude API calls fail.

    Examples:
        - Network timeouts
        - API authentication errors
        - Rate limiting
        - Service unavailable
    """
    pass


class ValidationError(InfraLLMError):
    """
    Raised when infrastructure requirements violate organizational policies.

    Attributes:
        violations: List of policy violation messages
    """

    def __init__(self, violations: List[str]):
        """
        Initialize ValidationError with list of violations.

        Args:
            violations: List of human-readable violation messages
        """
        self.violations = violations
        violation_count = len(violations)
        super().__init__(
            f"Policy validation failed: {violation_count} violation{'s' if violation_count != 1 else ''}"
        )


class ParsingError(InfraLLMError):
    """
    Raised when Claude's response cannot be parsed into valid infrastructure requirements.

    Examples:
        - Invalid JSON response
        - Missing required fields
        - Malformed data structures
    """
    pass
