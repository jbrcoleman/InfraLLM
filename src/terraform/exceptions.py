"""
Custom exceptions for Terraform code generation.

This module defines exceptions specific to the Terraform generation process.
"""


class TerraformGenerationError(Exception):
    """
    Raised when Terraform code generation fails.

    This exception is raised in various scenarios:
    - Template not found for resource type
    - Missing required parameters
    - Template rendering error
    - Invalid resource type

    Example:
        >>> raise TerraformGenerationError("Template not found for resource type 'invalid'")
        Traceback (most recent call last):
        ...
        TerraformGenerationError: Template not found for resource type 'invalid'
    """

    pass
