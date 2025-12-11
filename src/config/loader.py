"""
Configuration loader for InfraLLM policies.

This module provides functions to load and cache organizational policies
from the policies.yaml file.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

import yaml

from src.llm.exceptions import ConfigurationError


def _get_policies_path() -> Path:
    """
    Get the path to the policies.yaml file.

    Returns:
        Path to policies.yaml in the src/config directory
    """
    # Get the directory containing this file
    config_dir = Path(__file__).parent
    policies_path = config_dir / "policies.yaml"

    if not policies_path.exists():
        raise ConfigurationError(
            f"Policies file not found at: {policies_path}\n"
            "Please ensure src/config/policies.yaml exists."
        )

    return policies_path


def _validate_policies(policies: Dict[str, Any]) -> None:
    """
    Validate that the policies dictionary has the required structure.

    Args:
        policies: Loaded policies dictionary

    Raises:
        ConfigurationError: If policies are missing required sections
    """
    required_sections = ["naming", "tags", "security", "resources"]

    for section in required_sections:
        if section not in policies:
            raise ConfigurationError(
                f"Invalid policies.yaml: missing required section '{section}'"
            )

    # Validate naming section
    if "pattern" not in policies["naming"]:
        raise ConfigurationError(
            "Invalid policies.yaml: naming section missing 'pattern' field"
        )

    # Validate tags section
    if "required" not in policies["tags"]:
        raise ConfigurationError(
            "Invalid policies.yaml: tags section missing 'required' field"
        )

    if not isinstance(policies["tags"]["required"], list):
        raise ConfigurationError(
            "Invalid policies.yaml: tags.required must be a list"
        )


@lru_cache(maxsize=1)
def load_policies() -> Dict[str, Any]:
    """
    Load and cache organizational policies from policies.yaml.

    This function uses LRU cache to ensure policies are only loaded once
    during the application lifetime. The cache can be cleared for testing
    by calling load_policies.cache_clear().

    Returns:
        Dictionary containing organizational policies

    Raises:
        ConfigurationError: If policies file is missing or invalid

    Example:
        >>> policies = load_policies()
        >>> print(policies['naming']['pattern'])
        '{environment}-{application}-{resource}'
    """
    policies_path = _get_policies_path()

    try:
        with open(policies_path, 'r') as f:
            policies = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Failed to parse policies.yaml: {str(e)}\n"
            "Please ensure the file contains valid YAML."
        )
    except Exception as e:
        raise ConfigurationError(
            f"Failed to read policies.yaml: {str(e)}"
        )

    if not isinstance(policies, dict):
        raise ConfigurationError(
            "Invalid policies.yaml: root element must be a dictionary"
        )

    _validate_policies(policies)

    return policies


def reload_policies() -> Dict[str, Any]:
    """
    Force reload of policies from disk, bypassing cache.

    Useful for testing or when policies have been updated.

    Returns:
        Freshly loaded policies dictionary
    """
    load_policies.cache_clear()
    return load_policies()
