"""
Data models for Terraform code generation.

This module defines the data structures used to represent generated
Terraform code and associated metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from pathlib import Path


@dataclass
class GeneratedTerraform:
    """
    Container for generated Terraform files and metadata.

    Attributes:
        resource_type: Type of resource (s3, eks, rds, vpc)
        resource_name: Name of the resource
        environment: Target environment (dev, staging, prod)
        files: Dictionary mapping filenames to their contents
        metadata: Additional metadata (generation timestamp, versions, etc.)

    Example:
        >>> terraform = GeneratedTerraform(
        ...     resource_type="s3",
        ...     resource_name="staging-logs-bucket",
        ...     environment="staging",
        ...     files={
        ...         "main.tf": "resource \"aws_s3_bucket\" ...",
        ...         "variables.tf": "variable \"aws_region\" ...",
        ...         "outputs.tf": "output \"bucket_id\" ..."
        ...     },
        ...     metadata={"timestamp": "2025-12-17T10:30:00"}
        ... )
        >>> print(terraform.get_directory_name())
        terraform/staging/s3/staging-logs-bucket
    """

    resource_type: str
    resource_name: str
    environment: str
    files: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_file(self, filename: str) -> str:
        """
        Get content of a specific file.

        Args:
            filename: Name of the file (e.g., "main.tf")

        Returns:
            Content of the file

        Raises:
            KeyError: If file not found
        """
        return self.files[filename]

    def save_to_directory(self, directory: Path) -> List[Path]:
        """
        Write all files to a directory.

        Args:
            directory: Path to the directory where files should be written

        Returns:
            List of paths to created files

        Example:
            >>> terraform = GeneratedTerraform(...)
            >>> paths = terraform.save_to_directory(Path("./output"))
            >>> print(paths)
            [PosixPath('output/main.tf'), PosixPath('output/variables.tf'), ...]
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        created_paths = []
        for filename, content in self.files.items():
            file_path = directory / filename
            file_path.write_text(content)
            created_paths.append(file_path)

        return created_paths

    def format_for_display(self) -> str:
        """
        Format generated code for Rich console display.

        Returns:
            Formatted string suitable for terminal display
        """
        lines = []
        lines.append(f"Resource: {self.resource_type}")
        lines.append(f"Name: {self.resource_name}")
        lines.append(f"Environment: {self.environment}")
        lines.append(f"Files: {', '.join(self.files.keys())}")
        lines.append("")

        for filename, content in self.files.items():
            lines.append(f"=== {filename} ===")
            lines.append(content)
            lines.append("")

        return "\n".join(lines)

    def get_directory_name(self) -> str:
        """
        Get suggested directory name for generated Terraform.

        Returns:
            Directory path following pattern: terraform/{environment}/{resource_type}/{resource_name}

        Example:
            >>> terraform = GeneratedTerraform(
            ...     resource_type="eks",
            ...     resource_name="prod-api-cluster",
            ...     environment="prod",
            ...     files={},
            ...     metadata={}
            ... )
            >>> print(terraform.get_directory_name())
            terraform/prod/eks/prod-api-cluster
        """
        return f"terraform/{self.environment}/{self.resource_type}/{self.resource_name}"
