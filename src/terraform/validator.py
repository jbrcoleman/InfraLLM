"""
Parameter validation for Terraform template rendering.

This module validates that infrastructure requirements have all necessary
parameters for template rendering, catching errors before template generation.
"""

from typing import Dict, Any, List


def validate_s3_parameters(params: Dict[str, Any]) -> List[str]:
    """
    Validate S3 parameters have all required fields for template rendering.

    Args:
        params: S3 parameters from infrastructure request

    Returns:
        List of error messages (empty if valid)

    Example:
        >>> params = {"versioning": True, "encryption": "AES256"}
        >>> errors = validate_s3_parameters(params)
        >>> print(errors)
        ['Missing required S3 parameter: public_access_block']
    """
    errors = []
    required = ['versioning', 'encryption', 'public_access_block']

    for field in required:
        if field not in params:
            errors.append(f"Missing required S3 parameter: {field}")

    # Validate encryption value
    if 'encryption' in params:
        valid_encryption = ['AES256', 'aws:kms']
        if params['encryption'] not in valid_encryption:
            errors.append(
                f"S3 encryption must be one of {valid_encryption}, "
                f"got '{params['encryption']}'"
            )

    return errors


def validate_eks_parameters(params: Dict[str, Any]) -> List[str]:
    """
    Validate EKS parameters have all required fields for template rendering.

    Args:
        params: EKS parameters from infrastructure request

    Returns:
        List of error messages (empty if valid)

    Example:
        >>> params = {"kubernetes_version": "1.28"}
        >>> errors = validate_eks_parameters(params)
        >>> print(errors)
        ['EKS requires at least one node group', 'Missing required EKS parameter: private_endpoint']
    """
    errors = []

    # Check required top-level parameters
    if 'kubernetes_version' not in params:
        errors.append("Missing required EKS parameter: kubernetes_version")

    if 'node_groups' not in params or not params['node_groups']:
        errors.append("EKS requires at least one node group")
    else:
        # Validate each node group
        for i, ng in enumerate(params['node_groups']):
            required_ng_fields = ['name', 'instance_types', 'desired_size', 'min_size', 'max_size']
            for field in required_ng_fields:
                if field not in ng:
                    errors.append(f"Node group {i} ('{ng.get('name', 'unnamed')}'): missing required field '{field}'")

            # Validate scaling configuration
            if all(field in ng for field in ['desired_size', 'min_size', 'max_size']):
                if ng['desired_size'] < ng['min_size']:
                    errors.append(
                        f"Node group {i} ('{ng.get('name', 'unnamed')}'): "
                        f"desired_size ({ng['desired_size']}) cannot be less than "
                        f"min_size ({ng['min_size']})"
                    )
                if ng['desired_size'] > ng['max_size']:
                    errors.append(
                        f"Node group {i} ('{ng.get('name', 'unnamed')}'): "
                        f"desired_size ({ng['desired_size']}) cannot be greater than "
                        f"max_size ({ng['max_size']})"
                    )

            # Validate instance_types is a list
            if 'instance_types' in ng and not isinstance(ng['instance_types'], list):
                errors.append(
                    f"Node group {i} ('{ng.get('name', 'unnamed')}'): "
                    f"instance_types must be a list"
                )

    if 'private_endpoint' not in params:
        errors.append("Missing required EKS parameter: private_endpoint")

    # Check that public_endpoint is defined (can be true or false)
    if 'public_endpoint' not in params:
        # Not strictly required, but good practice
        pass  # We'll allow it to be optional and default to false

    return errors


def validate_rds_parameters(params: Dict[str, Any]) -> List[str]:
    """
    Validate RDS parameters have all required fields for template rendering.

    Note: RDS template not implemented yet in Phase 3, but validator included
    for future expansion.

    Args:
        params: RDS parameters from infrastructure request

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    required = [
        'engine',
        'engine_version',
        'instance_class',
        'allocated_storage',
        'backup_retention_period',
        'storage_encrypted'
    ]

    for field in required:
        if field not in params:
            errors.append(f"Missing required RDS parameter: {field}")

    return errors


def validate_vpc_parameters(params: Dict[str, Any]) -> List[str]:
    """
    Validate VPC parameters have all required fields for template rendering.

    Note: VPC template not implemented yet in Phase 3, but validator included
    for future expansion.

    Args:
        params: VPC parameters from infrastructure request

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    required = ['cidr_block', 'enable_dns_hostnames', 'enable_dns_support']

    for field in required:
        if field not in params:
            errors.append(f"Missing required VPC parameter: {field}")

    return errors
