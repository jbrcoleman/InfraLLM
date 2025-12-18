"""
GitHub integration for automated PR creation.

This module handles creating GitHub pull requests with generated Terraform code,
including branch creation, file commits, and PR description generation.
"""

import os
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from github import Github, GithubException
import anthropic

from src.git.exceptions import (
    ConfigurationError,
    BranchCreationError,
    CommitError,
    PullRequestError,
    RepositoryNotFoundError,
    GitHubError
)
from src.terraform.models import GeneratedTerraform


# Set up logging
logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Client for creating GitHub pull requests with generated Terraform code.
    """

    def __init__(self, token: str = None, org: str = None, repo: str = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token
            org: GitHub organization name
            repo: Repository name

        Raises:
            ConfigurationError: If required GitHub credentials are missing
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.org = org or os.getenv("GITHUB_ORG")
        self.repo = repo or os.getenv("GITHUB_REPO")

        if not all([self.token, self.org, self.repo]):
            raise ConfigurationError(
                "GITHUB_TOKEN, GITHUB_ORG, and GITHUB_REPO must be provided "
                "or set in environment.\n"
                "Check your .env file or set these environment variables."
            )

        # Initialize PyGithub client
        self.github = Github(self.token)
        logger.info(f"Initialized GitHub client for {self.org}/{self.repo}")

    def create_pr(
        self,
        terraform: GeneratedTerraform,
        requirements: Dict[str, Any],
        base_branch: str = "main",
    ) -> Dict[str, str]:
        """
        Create a GitHub pull request with generated Terraform code.

        Args:
            terraform: Generated Terraform code object
            requirements: Original infrastructure requirements for PR description
            base_branch: Base branch to create PR against (default: "main")

        Returns:
            Dictionary containing:
                - pr_url: URL of the created pull request
                - branch_name: Name of the created branch
                - pr_number: Pull request number

        Raises:
            RepositoryNotFoundError: If repository cannot be found
            BranchCreationError: If branch creation fails
            CommitError: If committing files fails
            PullRequestError: If PR creation fails

        Example:
            >>> client = GitHubClient()
            >>> terraform = GeneratedTerraform(...)
            >>> requirements = {'resource_type': 'rds', 'environment': 'prod'}
            >>> result = client.create_pr(terraform, requirements)
            >>> print(result['pr_url'])
            'https://github.com/org/repo/pull/123'
        """
        logger.info("Starting PR creation process")

        try:
            # Step 1: Get repository
            repo = self._get_repository()

            # Step 2: Create branch name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"infrallm/{terraform.environment}-{terraform.resource_type}-{terraform.resource_name}-{timestamp}"
            logger.info(f"Creating branch: {branch_name}")

            # Step 3: Get base branch reference
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
            base_sha = base_ref.object.sha

            # Step 4: Create new branch
            try:
                new_ref = repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=base_sha
                )
                logger.info(f"Created branch {branch_name} from {base_branch}")
            except GithubException as e:
                logger.error(f"Failed to create branch: {e}")
                raise BranchCreationError(
                    f"Failed to create branch '{branch_name}': {str(e)}"
                )

            # Step 4.5: Format Terraform files
            try:
                formatted_files = self._format_terraform_files(terraform.files)
                # Update terraform object with formatted files
                terraform.files = formatted_files
                logger.info(f"Formatted {len(formatted_files)} Terraform files")
            except Exception as e:
                logger.warning(f"Failed to format Terraform files: {e}")
                logger.info("Continuing with unformatted files")
                # Continue with original files if formatting fails

            # Step 5: Commit Terraform files
            directory = terraform.get_directory_name()
            commit_message = self._generate_commit_message(terraform, requirements)

            try:
                self._commit_files(
                    repo=repo,
                    branch_name=branch_name,
                    files=terraform.files,
                    directory=directory,
                    commit_message=commit_message
                )
                logger.info(f"Committed {len(terraform.files)} files to {branch_name}")
            except Exception as e:
                logger.error(f"Failed to commit files: {e}")
                raise CommitError(f"Failed to commit Terraform files: {str(e)}")

            # Step 6: Generate PR description
            pr_description = self.generate_pr_description(terraform, requirements)

            # Step 7: Create pull request
            pr_title = self._generate_pr_title(terraform, requirements)

            try:
                pr = repo.create_pull(
                    title=pr_title,
                    body=pr_description,
                    head=branch_name,
                    base=base_branch
                )
                logger.info(f"Created PR #{pr.number}: {pr.html_url}")

                # Step 8: Add labels if available
                try:
                    labels = self._get_labels(terraform, requirements)
                    if labels:
                        pr.add_to_labels(*labels)
                        logger.info(f"Added labels: {labels}")
                except Exception as e:
                    logger.warning(f"Failed to add labels: {e}")

                return {
                    "pr_url": pr.html_url,
                    "branch_name": branch_name,
                    "pr_number": str(pr.number)
                }

            except GithubException as e:
                logger.error(f"Failed to create PR: {e}")
                raise PullRequestError(f"Failed to create pull request: {str(e)}")

        except GithubException as e:
            if e.status == 404:
                raise RepositoryNotFoundError(
                    f"Repository '{self.org}/{self.repo}' not found. "
                    "Check your GITHUB_ORG and GITHUB_REPO settings."
                )
            raise GitHubError(f"GitHub API error: {str(e)}")

    def _get_repository(self):
        """
        Get the GitHub repository object.

        Returns:
            GitHub repository object

        Raises:
            RepositoryNotFoundError: If repository not found
        """
        try:
            repo_full_name = f"{self.org}/{self.repo}"
            repo = self.github.get_repo(repo_full_name)
            logger.debug(f"Retrieved repository: {repo_full_name}")
            return repo
        except GithubException as e:
            if e.status == 404:
                raise RepositoryNotFoundError(
                    f"Repository '{self.org}/{self.repo}' not found"
                )
            raise

    def _format_terraform_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """
        Format Terraform files using terraform fmt.

        Args:
            files: Dictionary mapping filenames to contents

        Returns:
            Dictionary with formatted file contents

        Raises:
            Exception: If terraform fmt fails (non-fatal, will be caught by caller)
        """
        # Check if terraform is installed
        try:
            result = subprocess.run(
                ["terraform", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                logger.warning("terraform command not found, skipping formatting")
                return files
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("terraform command not available, skipping formatting")
            return files

        # Create temporary directory for formatting
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            formatted_files = {}

            # Write files to temp directory
            for filename, content in files.items():
                if filename.endswith('.tf'):
                    file_path = temp_path / filename
                    file_path.write_text(content)
                    logger.debug(f"Wrote {filename} to temp directory")
                else:
                    # Non-.tf files don't need formatting
                    formatted_files[filename] = content

            # Run terraform fmt on all .tf files
            try:
                result = subprocess.run(
                    ["terraform", "fmt"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    logger.info("terraform fmt completed successfully")
                else:
                    logger.warning(f"terraform fmt returned non-zero exit code: {result.returncode}")
                    logger.debug(f"stderr: {result.stderr}")

            except subprocess.TimeoutExpired:
                logger.warning("terraform fmt timed out, using original files")
                return files

            # Read formatted files back
            for filename in files.keys():
                if filename.endswith('.tf'):
                    file_path = temp_path / filename
                    if file_path.exists():
                        formatted_content = file_path.read_text()
                        formatted_files[filename] = formatted_content
                        logger.debug(f"Read formatted {filename}")
                    else:
                        # If file doesn't exist, use original
                        formatted_files[filename] = files[filename]

            return formatted_files

    def _commit_files(
        self,
        repo,
        branch_name: str,
        files: Dict[str, str],
        directory: str,
        commit_message: str
    ):
        """
        Commit multiple files to a branch.

        Args:
            repo: GitHub repository object
            branch_name: Branch to commit to
            files: Dictionary mapping filenames to contents
            directory: Directory path for the files
            commit_message: Commit message
        """
        for filename, content in files.items():
            file_path = f"{directory}/{filename}"
            try:
                # Try to get existing file (in case we're updating)
                try:
                    existing_file = repo.get_contents(file_path, ref=branch_name)
                    repo.update_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        sha=existing_file.sha,
                        branch=branch_name
                    )
                    logger.debug(f"Updated file: {file_path}")
                except GithubException as e:
                    if e.status == 404:
                        # File doesn't exist, create it
                        repo.create_file(
                            path=file_path,
                            message=commit_message,
                            content=content,
                            branch=branch_name
                        )
                        logger.debug(f"Created file: {file_path}")
                    else:
                        raise
            except Exception as e:
                logger.error(f"Failed to commit {file_path}: {e}")
                raise

    def _generate_commit_message(
        self,
        terraform: GeneratedTerraform,
        requirements: Dict[str, Any]
    ) -> str:
        """
        Generate a commit message for the Terraform files.

        Args:
            terraform: Generated Terraform object
            requirements: Infrastructure requirements

        Returns:
            Commit message string
        """
        return (
            f"Add {terraform.environment} {terraform.resource_type}: {terraform.resource_name}\n\n"
            f"Generated Terraform code for infrastructure provisioning.\n"
            f"Resource type: {terraform.resource_type}\n"
            f"Environment: {terraform.environment}\n"
            f"Files: {', '.join(terraform.files.keys())}\n\n"
            f"Generated by InfraLLM"
        )

    def _generate_pr_title(
        self,
        terraform: GeneratedTerraform,
        requirements: Dict[str, Any]
    ) -> str:
        """
        Generate a PR title.

        Args:
            terraform: Generated Terraform object
            requirements: Infrastructure requirements

        Returns:
            PR title string
        """
        resource_type_display = terraform.resource_type.upper()
        return (
            f"[InfraLLM] Add {terraform.environment} {resource_type_display}: "
            f"{terraform.resource_name}"
        )

    def _get_labels(
        self,
        terraform: GeneratedTerraform,
        requirements: Dict[str, Any]
    ) -> list:
        """
        Get labels to apply to the PR.

        Args:
            terraform: Generated Terraform object
            requirements: Infrastructure requirements

        Returns:
            List of label names
        """
        labels = ["infrastructure", "terraform"]

        # Add environment label
        labels.append(f"env:{terraform.environment}")

        # Add resource type label
        labels.append(f"resource:{terraform.resource_type}")

        return labels

    def generate_pr_description(
        self,
        terraform: GeneratedTerraform,
        requirements: Dict[str, Any]
    ) -> str:
        """
        Generate PR description explaining the infrastructure changes.

        Uses Claude to create a detailed, human-readable description of what
        infrastructure is being provisioned and why.

        Args:
            terraform: Generated Terraform object
            requirements: Infrastructure requirements

        Returns:
            Markdown-formatted PR description
        """
        logger.info("Generating PR description with Claude")

        # Build context for Claude
        context = {
            "resource_type": terraform.resource_type,
            "resource_name": terraform.resource_name,
            "environment": terraform.environment,
            "parameters": requirements.get("parameters", {}),
            "tags": requirements.get("tags", {}),
            "files": list(terraform.files.keys())
        }

        # Create prompt for PR description
        prompt = f"""Generate a detailed GitHub Pull Request description for infrastructure provisioning.

Context:
- Resource Type: {context['resource_type'].upper()}
- Resource Name: {context['resource_name']}
- Environment: {context['environment']}
- Parameters: {context['parameters']}
- Tags: {context['tags']}
- Files Generated: {', '.join(context['files'])}

Create a PR description with:
1. Summary section explaining what infrastructure is being created
2. Resources Created section listing the key resources
3. Security Compliance section noting security features (encryption, access controls, etc.)
4. Review Checklist with checkboxes for reviewers

Format the output as GitHub-flavored Markdown with clear sections.
Make it professional and suitable for a platform engineering team.
"""

        try:
            # Get API key from environment
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not found, using template PR description")
                return self._generate_template_pr_description(terraform, requirements)

            client = anthropic.Anthropic(api_key=api_key)

            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                temperature=0.3,  # Slightly creative but still focused
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            pr_description = response.content[0].text
            logger.info("Successfully generated PR description with Claude")

            # Add footer
            pr_description += "\n\n---\n\nGenerated by [InfraLLM](https://github.com/your-org/infrallm)"

            return pr_description

        except Exception as e:
            logger.warning(f"Failed to generate PR description with Claude: {e}")
            logger.info("Falling back to template PR description")
            return self._generate_template_pr_description(terraform, requirements)

    def _generate_template_pr_description(
        self,
        terraform: GeneratedTerraform,
        requirements: Dict[str, Any]
    ) -> str:
        """
        Generate a template PR description (fallback when Claude is unavailable).

        Args:
            terraform: Generated Terraform object
            requirements: Infrastructure requirements

        Returns:
            Markdown-formatted PR description
        """
        parameters = requirements.get("parameters", {})
        tags = requirements.get("tags", {})

        # Format parameters
        params_list = "\n".join([f"- **{k}**: {v}" for k, v in parameters.items()])

        # Format tags
        tags_list = "\n".join([f"- {k}: {v}" for k, v in tags.items()])

        description = f"""## Infrastructure Provisioning Request

### Summary
Provisioning **{terraform.resource_type.upper()}** resource `{terraform.resource_name}` in **{terraform.environment}** environment.

### Resources Created
{params_list}

### Tags Applied
{tags_list}

### Files Generated
{chr(10).join([f'- `{filename}`' for filename in terraform.files.keys()])}

### Security Compliance
- Encryption at rest enabled
- Following organizational security policies
- Required tags applied

### Review Checklist
- [ ] Resource sizing is appropriate
- [ ] Environment is correct
- [ ] Tags are complete
- [ ] Security settings reviewed
- [ ] Cost impact acceptable

---

Generated by [InfraLLM](https://github.com/your-org/infrallm)
"""
        return description
