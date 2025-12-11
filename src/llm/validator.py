"""
Policy validation for infrastructure requests.

This module validates parsed infrastructure requests against organizational
policies to ensure compliance before generating Terraform code.
"""

import re
from typing import Dict, Any, List, Optional

from src.llm.models import InfrastructureRequest


def validate_naming_pattern(
    resource_name: str,
    pattern: str,
    environment: str,
    resource_type: str
) -> Optional[str]:
    """
    Validate that resource name follows the organizational naming convention.

    Args:
        resource_name: The name to validate
        pattern: The naming pattern (e.g., "{environment}-{application}-{resource}")
        environment: The target environment
        resource_type: The type of resource

    Returns:
        Error message if validation fails, None if valid

    Example:
        >>> validate_naming_pattern("prod-api-db", "{environment}-{application}-{resource}", "prod", "rds")
        None
        >>> validate_naming_pattern("db-prod", "{environment}-{application}-{resource}", "prod", "rds")
        'Naming violation: Expected format {environment}-{application}-{resource}, got db-prod'
    """
    # Pattern should start with the environment
    if not resource_name.startswith(f"{environment}-"):
        return (
            f"Naming violation: Resource name must start with environment '{environment}', "
            f"got '{resource_name}'"
        )

    # Check the pattern has at least 3 parts (env-app-resource)
    parts = resource_name.split("-")
    if len(parts) < 3:
        return (
            f"Naming violation: Expected format '{pattern}' with at least 3 parts "
            f"(environment-application-resource), got '{resource_name}' with {len(parts)} parts"
        )

    return None


def validate_required_tags(
    tags: Dict[str, str],
    required_tags: List[str]
) -> List[str]:
    """
    Validate that all required tags are present.

    Args:
        tags: Tags dictionary from infrastructure request
        required_tags: List of required tag names from policies

    Returns:
        List of error messages for missing tags (empty if all present)

    Example:
        >>> tags = {"Environment": "prod", "Owner": "team"}
        >>> required = ["Environment", "Owner", "CostCenter"]
        >>> errors = validate_required_tags(tags, required)
        >>> print(errors)
        ['Missing required tag: CostCenter']
    """
    violations = []

    for required_tag in required_tags:
        if required_tag not in tags:
            violations.append(f"Missing required tag: {required_tag}")
        elif not tags[required_tag] or not str(tags[required_tag]).strip():
            violations.append(f"Required tag '{required_tag}' cannot be empty")

    return violations


def validate_rds_constraints(
    parameters: Dict[str, Any],
    policies: Dict[str, Any]
) -> List[str]:
    """
    Validate RDS-specific constraints.

    Args:
        parameters: RDS parameters from infrastructure request
        policies: RDS policies from policies.yaml

    Returns:
        List of policy violations (empty if valid)
    """
    violations = []
    rds_policies = policies.get("rds", {})

    # Validate engine
    allowed_engines = rds_policies.get("allowed_engines", ["postgres", "mysql"])
    engine = parameters.get("engine", "").lower()

    if engine not in allowed_engines:
        violations.append(
            f"RDS: Engine '{engine}' not allowed. "
            f"Allowed engines: {', '.join(allowed_engines)}"
        )

    # Validate backup retention
    min_backup_days = rds_policies.get("min_backup_days", 7)
    backup_retention = parameters.get("backup_retention_period", 0)

    if backup_retention < min_backup_days:
        violations.append(
            f"RDS: Backup retention period ({backup_retention} days) is less than "
            f"required minimum ({min_backup_days} days)"
        )

    # Validate encryption
    if rds_policies.get("encryption", True):
        storage_encrypted = parameters.get("storage_encrypted", False)
        if not storage_encrypted:
            violations.append(
                "RDS: Storage encryption is required by organizational policy"
            )

    return violations


def validate_s3_constraints(
    parameters: Dict[str, Any],
    policies: Dict[str, Any]
) -> List[str]:
    """
    Validate S3-specific constraints.

    Args:
        parameters: S3 parameters from infrastructure request
        policies: S3 policies from policies.yaml

    Returns:
        List of policy violations (empty if valid)
    """
    violations = []
    s3_policies = policies.get("s3", {})

    # Validate versioning
    if s3_policies.get("versioning", True):
        versioning = parameters.get("versioning", False)
        if not versioning:
            violations.append(
                "S3: Versioning is required by organizational policy"
            )

    # Validate encryption
    required_encryption = s3_policies.get("encryption", "AES256")
    encryption = parameters.get("encryption", "")

    if encryption != required_encryption:
        violations.append(
            f"S3: Encryption must be '{required_encryption}', got '{encryption}'"
        )

    return violations


def validate_eks_constraints(
    parameters: Dict[str, Any],
    policies: Dict[str, Any]
) -> List[str]:
    """
    Validate EKS-specific constraints.

    Args:
        parameters: EKS parameters from infrastructure request
        policies: EKS policies from policies.yaml

    Returns:
        List of policy violations (empty if valid)
    """
    violations = []
    eks_policies = policies.get("eks", {})

    # Validate minimum nodes
    min_nodes = eks_policies.get("min_nodes", 2)

    # Check node groups for total desired size
    node_groups = parameters.get("node_groups", [])
    total_nodes = sum(ng.get("desired_size", 0) for ng in node_groups)

    if total_nodes < min_nodes:
        violations.append(
            f"EKS: Total desired nodes ({total_nodes}) is less than "
            f"required minimum ({min_nodes} nodes)"
        )

    # Validate private endpoint
    if eks_policies.get("private_endpoint", True):
        private_endpoint = parameters.get("private_endpoint", False)
        if not private_endpoint:
            violations.append(
                "EKS: Private endpoint is required by organizational policy"
            )

    return violations


def validate_request(
    request: InfrastructureRequest,
    policies: Dict[str, Any]
) -> List[str]:
    """
    Validate infrastructure request against all organizational policies.

    Args:
        request: Validated Pydantic model of infrastructure request
        policies: Organizational policies from policies.yaml

    Returns:
        List of policy violation messages (empty list if valid)

    Example:
        >>> from src.llm.models import InfrastructureRequest
        >>> request = InfrastructureRequest(
        ...     resource_type="rds",
        ...     resource_name="prod-api-db",
        ...     parameters={"engine": "postgres"},
        ...     environment="prod",
        ...     tags={"Environment": "prod"}
        ... )
        >>> violations = validate_request(request, policies)
        >>> if violations:
        ...     print("Violations found:", violations)
    """
    violations = []

    # Validate naming pattern
    naming_pattern = policies.get("naming", {}).get("pattern", "")
    naming_error = validate_naming_pattern(
        request.resource_name,
        naming_pattern,
        request.environment,
        request.resource_type
    )
    if naming_error:
        violations.append(naming_error)

    # Validate required tags
    required_tags = policies.get("tags", {}).get("required", [])
    tag_violations = validate_required_tags(request.tags, required_tags)
    violations.extend(tag_violations)

    # Validate resource-specific constraints
    resource_policies = policies.get("resources", {})

    if request.resource_type == "rds":
        rds_violations = validate_rds_constraints(request.parameters, resource_policies)
        violations.extend(rds_violations)

    elif request.resource_type == "s3":
        s3_violations = validate_s3_constraints(request.parameters, resource_policies)
        violations.extend(s3_violations)

    elif request.resource_type == "eks":
        eks_violations = validate_eks_constraints(request.parameters, resource_policies)
        violations.extend(eks_violations)

    return violations
