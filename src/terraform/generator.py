"""
Terraform code generator.

This module generates Terraform HCL code from structured infrastructure requirements
using Jinja2 templates.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import jinja2
from jinja2 import Template, Environment, FileSystemLoader, TemplateError

from src.terraform.models import GeneratedTerraform
from src.terraform.exceptions import TerraformGenerationError
from src.terraform.validator import (
    validate_s3_parameters,
    validate_eks_parameters,
    validate_rds_parameters,
    validate_vpc_parameters
)
from src.config.loader import load_policies


class TerraformGenerator:
    """
    Generates Terraform HCL code from structured infrastructure requirements.

    This class uses Jinja2 templates to convert the JSON output from Claude API
    into production-ready Terraform code with organizational standards.

    Example:
        >>> generator = TerraformGenerator()
        >>> requirements = {
        ...     "resource_type": "s3",
        ...     "resource_name": "staging-logs-bucket",
        ...     "parameters": {"versioning": True, "encryption": "AES256", ...},
        ...     "environment": "staging",
        ...     "tags": {"Environment": "staging", ...}
        ... }
        >>> terraform = generator.generate(requirements)
        >>> print(terraform.files.keys())
        dict_keys(['main.tf', 'variables.tf', 'outputs.tf', 'provider.tf', 'backend.tf'])
    """

    def __init__(self, templates_dir: str = None):
        """
        Initialize Terraform generator with Jinja2 environment.

        Args:
            templates_dir: Override default template directory.
                          Defaults to src/terraform/templates

        Raises:
            TerraformGenerationError: If templates directory doesn't exist
        """
        # Determine templates directory
        if templates_dir is None:
            # Default to src/terraform/templates relative to this file
            current_dir = Path(__file__).parent
            templates_dir = current_dir / "templates"
        else:
            templates_dir = Path(templates_dir)

        if not templates_dir.exists():
            raise TerraformGenerationError(
                f"Templates directory not found: {templates_dir}\n"
                "Please ensure templates are created before using the generator."
            )

        self.templates_dir = templates_dir

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

        # Add custom filters
        self.env.filters['terraform_bool'] = lambda x: 'true' if x else 'false'
        self.env.filters['sanitize_identifier'] = lambda x: x.replace('-', '_')

    def generate(self, requirements: Dict[str, Any]) -> GeneratedTerraform:
        """
        Generate Terraform code from structured requirements.

        This is the main entry point for Terraform code generation. It orchestrates:
        1. Validation of requirements structure
        2. Validation of resource type support
        3. Parameter validation for the specific resource type
        4. Template loading
        5. Context preparation
        6. Template rendering
        7. Return of GeneratedTerraform object

        Args:
            requirements: Structured infrastructure requirements from Claude API
                         Must include: resource_type, resource_name, parameters,
                         environment, tags

        Returns:
            GeneratedTerraform object containing all generated Terraform files

        Raises:
            TerraformGenerationError: If generation fails at any step

        Example:
            >>> generator = TerraformGenerator()
            >>> requirements = {...}  # From ClaudeClient.parse_infrastructure_request()
            >>> terraform = generator.generate(requirements)
            >>> terraform.save_to_directory(Path("./output"))
        """
        # Step 1: Validate requirements structure
        required_fields = ['resource_type', 'resource_name', 'parameters', 'environment', 'tags']
        for field in required_fields:
            if field not in requirements:
                raise TerraformGenerationError(
                    f"Missing required field '{field}' in requirements"
                )

        resource_type = requirements['resource_type']

        # Step 2: Validate resource type is supported
        supported_types = ['s3', 'eks', 'rds', 'vpc']
        if resource_type not in supported_types:
            raise TerraformGenerationError(
                f"Unsupported resource type '{resource_type}'. "
                f"Supported types: {', '.join(supported_types)}"
            )

        # Step 3: Validate parameters for this resource type
        validation_func = {
            's3': validate_s3_parameters,
            'eks': validate_eks_parameters,
            'rds': validate_rds_parameters,
            'vpc': validate_vpc_parameters
        }.get(resource_type)

        if validation_func:
            param_errors = validation_func(requirements.get('parameters', {}))
            if param_errors:
                raise TerraformGenerationError(
                    f"Invalid parameters for {resource_type}:\n" +
                    "\n".join(f"  - {err}" for err in param_errors)
                )

        # Step 4: Load templates
        try:
            templates = self._load_templates(resource_type)
        except FileNotFoundError as e:
            raise TerraformGenerationError(
                f"Templates not found for resource type '{resource_type}': {str(e)}\n"
                f"Expected templates in: {self.templates_dir / resource_type}"
            )
        except TemplateError as e:
            raise TerraformGenerationError(
                f"Failed to load templates for '{resource_type}': {str(e)}"
            )

        # Step 5: Prepare context
        try:
            context = self._prepare_context(requirements)
        except Exception as e:
            raise TerraformGenerationError(
                f"Failed to prepare template context: {str(e)}"
            )

        # Step 6: Render all templates
        files = {}
        try:
            for filename, template in templates.items():
                files[filename] = self._render_template(template, context)
        except TemplateError as e:
            raise TerraformGenerationError(
                f"Template rendering failed: {str(e)}"
            )
        except Exception as e:
            raise TerraformGenerationError(
                f"Unexpected error during rendering: {str(e)}"
            )

        # Step 7: Return GeneratedTerraform object
        return GeneratedTerraform(
            resource_type=resource_type,
            resource_name=requirements['resource_name'],
            environment=requirements['environment'],
            files=files,
            metadata={
                'timestamp': context['generated_at'],
                'policy_version': '1.0',
                'generator_version': '0.1.0',
                'template_dir': str(self.templates_dir)
            }
        )

    def _load_templates(self, resource_type: str) -> Dict[str, Template]:
        """
        Load Jinja2 templates for the specified resource type.

        Loads both resource-specific templates (main.tf.j2, variables.tf.j2, outputs.tf.j2)
        and common templates (provider.tf.j2, backend.tf.j2).

        Args:
            resource_type: Type of resource (s3, eks, rds, vpc)

        Returns:
            Dictionary mapping output filenames to loaded Jinja2 Template objects

        Raises:
            FileNotFoundError: If required templates are missing
            TemplateError: If template loading fails
        """
        templates = {}

        # Load resource-specific templates
        resource_dir = Path(self.templates_dir) / resource_type
        for template_file in ['main.tf.j2', 'variables.tf.j2', 'outputs.tf.j2']:
            template_path = resource_dir / template_file
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Required template not found: {template_path}"
                )

            # Load template using Jinja2 environment
            template_name = f"{resource_type}/{template_file}"
            templates[template_file.replace('.j2', '')] = self.env.get_template(template_name)

        # Load common templates
        common_dir = Path(self.templates_dir) / '_common'
        for template_file in ['provider.tf.j2', 'backend.tf.j2']:
            template_path = common_dir / template_file
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Required common template not found: {template_path}"
                )

            template_name = f"_common/{template_file}"
            templates[template_file.replace('.j2', '')] = self.env.get_template(template_name)

        return templates

    def _prepare_context(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare Jinja2 rendering context with defaults and computed values.

        Enhances the raw requirements with additional data needed for template rendering:
        - Organization name from policies
        - VPC variable references (for EKS, RDS)
        - Generation timestamp
        - Sanitized resource name for Terraform identifiers

        Args:
            requirements: Raw requirements from Claude API

        Returns:
            Enhanced context dictionary ready for template rendering
        """
        context = requirements.copy()

        # Add organization name from config
        try:
            policies = load_policies()
            org_name = policies.get('organization', {}).get('name', 'your-organization')
            context['organization'] = org_name.lower().replace(' ', '-')
        except Exception:
            # Fallback if policies can't be loaded
            context['organization'] = 'your-organization'

        # Add VPC references for resources that need them
        if requirements['resource_type'] in ['eks', 'rds']:
            context['needs_vpc'] = True
        else:
            context['needs_vpc'] = False

        # Add timestamp
        context['generated_at'] = datetime.utcnow().isoformat()

        # Add sanitized resource name for Terraform identifiers
        # Terraform identifiers don't allow hyphens, so convert to underscores
        context['tf_resource_name'] = requirements['resource_name'].replace('-', '_')

        return context

    def _render_template(self, template: Template, context: Dict[str, Any]) -> str:
        """
        Render a single Jinja2 template with error handling.

        Args:
            template: Jinja2 Template object
            context: Context dictionary for rendering

        Returns:
            Rendered template content as string

        Raises:
            TemplateError: If rendering fails
        """
        try:
            rendered = template.render(**context)
            return rendered
        except TemplateError as e:
            # Re-raise Jinja2 errors with context
            raise TemplateError(f"Error rendering template: {str(e)}")
