"""
Pydantic models for infrastructure request validation.

This module defines the data models used to validate Claude's output
and ensure it conforms to the expected schema.
"""

from typing import Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class InfrastructureRequest(BaseModel):
    """
    Structured infrastructure provisioning request.

    This model represents a validated infrastructure request with all
    required fields and organizational standards enforced.

    Attributes:
        resource_type: Type of infrastructure resource
        resource_name: Name following organizational naming convention
        parameters: Resource-specific configuration parameters
        environment: Target environment for deployment
        tags: Organizational tags for resource tagging
    """

    resource_type: Literal["rds", "s3", "eks", "vpc"] = Field(
        description="Type of infrastructure resource to provision"
    )

    resource_name: str = Field(
        description="Resource name following naming convention: {environment}-{application}-{resource}",
        min_length=3,
        max_length=63
    )

    parameters: Dict[str, Any] = Field(
        description="Resource-specific configuration parameters",
        default_factory=dict
    )

    environment: Literal["dev", "staging", "prod"] = Field(
        description="Target environment for deployment"
    )

    tags: Dict[str, str] = Field(
        description="Organizational tags for resource tagging",
        default_factory=dict
    )

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name_not_empty(cls, v: str) -> str:
        """
        Validate that resource_name is not empty or whitespace.

        Args:
            v: Resource name value

        Returns:
            Validated resource name

        Raises:
            ValueError: If resource name is empty or only whitespace
        """
        if not v or not v.strip():
            raise ValueError("resource_name cannot be empty or whitespace")
        return v.strip()

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name_format(cls, v: str) -> str:
        """
        Validate that resource_name uses lowercase and hyphens.

        Args:
            v: Resource name value

        Returns:
            Validated resource name

        Raises:
            ValueError: If resource name contains invalid characters
        """
        if not all(c.islower() or c.isdigit() or c == '-' for c in v):
            raise ValueError(
                "resource_name must contain only lowercase letters, numbers, and hyphens"
            )
        return v

    @field_validator('parameters')
    @classmethod
    def validate_parameters_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that parameters dictionary is not empty.

        Args:
            v: Parameters dictionary

        Returns:
            Validated parameters

        Raises:
            ValueError: If parameters is empty
        """
        if not v:
            raise ValueError("parameters cannot be empty - at least one parameter is required")
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags_not_empty(cls, v: Dict[str, str]) -> Dict[str, str]:
        """
        Validate that tags dictionary is not empty.

        Args:
            v: Tags dictionary

        Returns:
            Validated tags

        Raises:
            ValueError: If tags is empty
        """
        if not v:
            raise ValueError("tags cannot be empty - required organizational tags must be present")
        return v

    class Config:
        """Pydantic model configuration."""
        # Allow extra fields for forward compatibility
        extra = "allow"
        # Use enum values instead of enum members
        use_enum_values = True
