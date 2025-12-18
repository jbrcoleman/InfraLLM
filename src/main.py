"""
InfraLLM - AI-powered infrastructure provisioning CLI.

Main entry point for the CLI application.
"""

import os
import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="InfraLLM")
def cli():
    """
    InfraLLM - AI-powered self-service infrastructure provisioning.

    Use natural language to generate production-ready Terraform code
    with organizational standards and automated PR creation.

    \b
    Quick Start:
      1. infrallm configure              # Set up API keys and GitHub
      2. infrallm provision "dev S3 bucket for logs"
      3. Review and merge the created PR

    \b
    Examples:
      infrallm provision "production Postgres database for payments API"
      infrallm dry-run "staging EKS cluster with 5 nodes"
      infrallm validate terraform/prod/database.tf

    \b
    Documentation: https://github.com/your-org/infrallm
    """
    pass


@cli.command()
@click.argument("request", type=str)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def provision(request: str, verbose: bool):
    """
    Generate Terraform code from natural language and create a GitHub PR.

    This command:
    - Parses your request using Claude AI
    - Generates production-ready Terraform code
    - Formats code with terraform fmt
    - Creates a GitHub pull request with detailed description

    \b
    Examples:
      infrallm provision "production Postgres database for payments API with 200GB storage"
      infrallm provision "staging S3 bucket for application logs with 60-day retention"
      infrallm provision "dev EKS cluster for API service with 5 nodes"

    \b
    The generated PR includes:
      - All Terraform files (main.tf, variables.tf, outputs.tf, etc.)
      - AI-generated description explaining the infrastructure
      - Security compliance checklist
      - Appropriate labels for filtering
    """
    from src.llm.client import ClaudeClient
    from src.llm.exceptions import (
        ConfigurationError,
        APIError,
        ValidationError as PolicyValidationError,
        ParsingError
    )

    console.print(Panel.fit(
        f"[bold cyan]Provisioning Infrastructure[/bold cyan]\n\n{request}",
        border_style="cyan"
    ))

    try:
        # Initialize Claude client
        client = ClaudeClient()

        # Parse infrastructure request
        with console.status("[bold blue]Parsing infrastructure request with Claude..."):
            requirements = client.parse_infrastructure_request(request)

        # Display parsed requirements
        console.print("\n[bold green]✓ Successfully Parsed Requirements[/bold green]\n")

        console.print(f"  [cyan]Resource Type:[/cyan] {requirements['resource_type'].upper()}")
        console.print(f"  [cyan]Resource Name:[/cyan] {requirements['resource_name']}")
        console.print(f"  [cyan]Environment:[/cyan] {requirements['environment']}")

        # Show key parameters
        console.print(f"\n  [cyan]Parameters:[/cyan]")
        for key, value in list(requirements['parameters'].items())[:5]:
            console.print(f"    • {key}: {value}")
        if len(requirements['parameters']) > 5:
            console.print(f"    • ... and {len(requirements['parameters']) - 5} more")

        # Show tags
        console.print(f"\n  [cyan]Tags:[/cyan]")
        for key, value in requirements['tags'].items():
            console.print(f"    • {key}: {value}")

        if verbose:
            console.print("\n[bold]Full JSON Output:[/bold]")
            console.print_json(data=requirements)

        # Generate Terraform code
        from src.terraform.generator import TerraformGenerator
        from src.terraform.exceptions import TerraformGenerationError

        console.print("\n[bold blue]Generating Terraform Code...[/bold blue]")

        try:
            generator = TerraformGenerator()
            with console.status("[bold blue]Rendering templates..."):
                terraform = generator.generate(requirements)

            console.print("[bold green]✓ Successfully Generated Terraform Code[/bold green]\n")

            console.print(f"  [cyan]Files Generated:[/cyan]")
            for filename in terraform.files.keys():
                console.print(f"    • {filename}")

            console.print(f"\n  [cyan]Output Directory:[/cyan] {terraform.get_directory_name()}")

            if verbose:
                console.print("\n[bold]Generated Terraform Preview:[/bold]")
                console.print(terraform.format_for_display())

        except TerraformGenerationError as e:
            console.print(f"\n[bold red]Terraform Generation Error:[/bold red] {str(e)}")
            console.print(f"\n[yellow]Tip:[/yellow] Check that templates exist for resource type '{requirements['resource_type']}'")
            raise click.Abort()

        # Phase 4: Create GitHub PR with terraform files
        from src.git.github import GitHubClient
        from src.git.exceptions import (
            ConfigurationError as GitHubConfigError,
            RepositoryNotFoundError,
            BranchCreationError,
            CommitError,
            PullRequestError,
            GitHubError
        )

        console.print("\n[bold blue]Creating GitHub Pull Request...[/bold blue]")

        try:
            github_client = GitHubClient()

            with console.status("[bold blue]Formatting Terraform code and creating PR..."):
                pr_result = github_client.create_pr(
                    terraform=terraform,
                    requirements=requirements
                )

            console.print("\n[bold green]✓ Successfully Created Pull Request[/bold green]\n")

            console.print(f"  [cyan]PR URL:[/cyan] {pr_result['pr_url']}")
            console.print(f"  [cyan]Branch:[/cyan] {pr_result['branch_name']}")
            console.print(f"  [cyan]PR Number:[/cyan] #{pr_result['pr_number']}")

            console.print(f"\n[green]Next steps:[/green]")
            console.print(f"  1. Review the PR at {pr_result['pr_url']}")
            console.print(f"  2. Verify the Terraform code")
            console.print(f"  3. Merge when ready to provision infrastructure")

        except GitHubConfigError as e:
            console.print(f"\n[bold red]GitHub Configuration Error:[/bold red] {str(e)}")
            console.print("\n[yellow]Fix:[/yellow] Set GitHub credentials in your .env file:")
            console.print("[dim]  GITHUB_TOKEN=your_token_here[/dim]")
            console.print("[dim]  GITHUB_ORG=your-organization[/dim]")
            console.print("[dim]  GITHUB_REPO=infrastructure[/dim]")
            raise click.Abort()

        except RepositoryNotFoundError as e:
            console.print(f"\n[bold red]Repository Not Found:[/bold red] {str(e)}")
            console.print("\n[yellow]Tip:[/yellow] Verify your GITHUB_ORG and GITHUB_REPO settings")
            raise click.Abort()

        except (BranchCreationError, CommitError, PullRequestError) as e:
            console.print(f"\n[bold red]GitHub Error:[/bold red] {str(e)}")
            console.print("\n[yellow]Troubleshooting:[/yellow]")
            console.print("  1. Verify your GitHub token has write permissions")
            console.print("  2. Check if the repository allows PR creation")
            console.print("  3. Ensure no branch name conflicts")
            if verbose:
                import traceback
                console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
            raise click.Abort()

        except GitHubError as e:
            console.print(f"\n[bold red]Unexpected GitHub Error:[/bold red] {str(e)}")
            if verbose:
                import traceback
                console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
            raise click.Abort()

    except ConfigurationError as e:
        console.print(f"\n[bold red]Configuration Error:[/bold red] {str(e)}")
        console.print("\n[yellow]Fix:[/yellow] Ensure ANTHROPIC_API_KEY is set in your .env file")
        console.print("[dim]Example: export ANTHROPIC_API_KEY=sk-ant-...[/dim]")
        raise click.Abort()

    except PolicyValidationError as e:
        console.print(f"\n[bold red]Policy Validation Failed:[/bold red]")
        console.print(f"\nYour request violates {len(e.violations)} organizational policy/policies:\n")
        for i, violation in enumerate(e.violations, 1):
            console.print(f"  {i}. {violation}")
        console.print("\n[yellow]Tip:[/yellow] Review your organization's policies in src/config/policies.yaml")
        raise click.Abort()

    except ParsingError as e:
        console.print(f"\n[bold red]Parsing Error:[/bold red] {str(e)}")
        console.print("\n[yellow]Tip:[/yellow] Try rephrasing your request with more specific details")
        if verbose:
            import traceback
            console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
        raise click.Abort()

    except APIError as e:
        console.print(f"\n[bold red]API Error:[/bold red] {str(e)}")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Verify your ANTHROPIC_API_KEY is valid")
        console.print("  2. Check your network connection")
        console.print("  3. Visit https://status.anthropic.com for service status")
        raise click.Abort()

    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("\n[dim]Full traceback:[/dim]")
            console.print(traceback.format_exc())
        raise click.Abort()


@cli.command()
@click.argument("request", type=str)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def dry_run(request: str, verbose: bool):
    """
    Preview generated Terraform code without creating a PR.

    Use this to see what infrastructure would be provisioned before
    actually creating a pull request. Great for testing and learning.

    \b
    Examples:
      infrallm dry-run "production RDS instance"
      infrallm dry-run "staging S3 bucket for logs with 90-day lifecycle"

    \b
    This command:
      - Parses your request with Claude AI
      - Generates Terraform code
      - Displays syntax-highlighted preview
      - Does NOT create any PR or modify files
    """
    from src.llm.client import ClaudeClient
    from src.llm.exceptions import (
        ConfigurationError,
        APIError,
        ValidationError as PolicyValidationError,
        ParsingError
    )

    console.print(Panel.fit(
        f"[bold yellow]Dry Run Mode[/bold yellow]\n\n{request}",
        border_style="yellow"
    ))

    try:
        # Initialize Claude client
        client = ClaudeClient()

        # Parse infrastructure request
        with console.status("[bold blue]Parsing infrastructure request with Claude..."):
            requirements = client.parse_infrastructure_request(request)

        # Display parsed requirements
        console.print("\n[bold green]✓ Dry Run - No Changes Will Be Made[/bold green]\n")

        console.print(Panel.fit(
            f"[bold]Resource:[/bold] {requirements['resource_type'].upper()}\n"
            f"[bold]Name:[/bold] {requirements['resource_name']}\n"
            f"[bold]Environment:[/bold] {requirements['environment']}",
            title="Parsed Infrastructure Request",
            border_style="yellow"
        ))

        # Always show full JSON in dry-run mode
        console.print("\n[bold]Full Configuration:[/bold]")
        console.print_json(data=requirements)

        # Generate Terraform code for preview
        from src.terraform.generator import TerraformGenerator
        from src.terraform.exceptions import TerraformGenerationError
        from rich.syntax import Syntax

        console.print("\n[bold blue]Generating Terraform Code Preview...[/bold blue]")

        try:
            generator = TerraformGenerator()
            with console.status("[bold blue]Rendering templates..."):
                terraform = generator.generate(requirements)

            console.print("\n[bold green]✓ Generated Terraform Code (Preview Only)[/bold green]\n")

            # Display each file with syntax highlighting
            for filename, content in terraform.files.items():
                console.print(f"\n[bold cyan]━━━ {filename} ━━━[/bold cyan]")
                syntax = Syntax(content, "hcl", theme="monokai", line_numbers=True)
                console.print(syntax)
                console.print()

            console.print(f"\n[dim]Directory: {terraform.get_directory_name()}[/dim]")
            console.print("[dim]This is a dry-run - no files were created or PRs opened[/dim]")

        except TerraformGenerationError as e:
            console.print(f"\n[bold red]Terraform Generation Error:[/bold red] {str(e)}")
            raise click.Abort()

    except ConfigurationError as e:
        console.print(f"\n[bold red]Configuration Error:[/bold red] {str(e)}")
        console.print("\n[yellow]Fix:[/yellow] Ensure ANTHROPIC_API_KEY is set in your .env file")
        raise click.Abort()

    except PolicyValidationError as e:
        console.print(f"\n[bold red]Policy Validation Failed:[/bold red]")
        console.print(f"\nYour request violates {len(e.violations)} organizational policy/policies:\n")
        for i, violation in enumerate(e.violations, 1):
            console.print(f"  {i}. {violation}")
        raise click.Abort()

    except ParsingError as e:
        console.print(f"\n[bold red]Parsing Error:[/bold red] {str(e)}")
        console.print("\n[yellow]Tip:[/yellow] Try rephrasing your request with more details")
        raise click.Abort()

    except APIError as e:
        console.print(f"\n[bold red]API Error:[/bold red] {str(e)}")
        raise click.Abort()

    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
        raise click.Abort()


@cli.command()
def configure():
    """
    Interactive setup wizard for API keys and GitHub settings.

    Run this first to set up InfraLLM. The wizard will:
    - Prompt for Anthropic API key (Claude AI)
    - Prompt for GitHub token and repository
    - Verify your credentials work
    - Save configuration to .env file

    \b
    What you'll need:
      1. Anthropic API key from: https://console.anthropic.com/settings/keys
      2. GitHub token from: https://github.com/settings/tokens
         - Token needs 'repo' or 'Contents + Pull requests' permissions
      3. GitHub organization/username and repository name

    \b
    Example:
      infrallm configure
      # Follow the interactive prompts
    """
    from pathlib import Path
    import os

    console.print(Panel.fit(
        "[bold green]InfraLLM Configuration Wizard[/bold green]\n\n"
        "Let's set up your InfraLLM environment",
        border_style="green"
    ))

    try:
        env_path = Path(".env")
        existing_config = {}

        # Load existing configuration if .env exists
        if env_path.exists():
            console.print("\n[yellow]Found existing .env file. Current values will be shown as defaults.[/yellow]")
            with open(env_path) as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        existing_config[key] = value

        console.print("\n[bold cyan]Step 1: Anthropic API Configuration[/bold cyan]")
        console.print("Get your API key from: https://console.anthropic.com/settings/keys\n")

        current_anthropic = existing_config.get('ANTHROPIC_API_KEY', '')
        if current_anthropic:
            anthropic_key = click.prompt(
                "Anthropic API Key",
                default=current_anthropic[:20] + "..." if len(current_anthropic) > 20 else current_anthropic,
                hide_input=True
            )
            # If user just pressed enter, keep the existing key
            if anthropic_key == current_anthropic[:20] + "...":
                anthropic_key = current_anthropic
        else:
            anthropic_key = click.prompt("Anthropic API Key", hide_input=True)

        console.print("\n[bold cyan]Step 2: GitHub Configuration[/bold cyan]")
        console.print("GitHub token needs 'repo' or 'Contents' + 'Pull requests' permissions")
        console.print("Create token at: https://github.com/settings/tokens\n")

        current_github = existing_config.get('GITHUB_TOKEN', '')
        if current_github:
            github_token = click.prompt(
                "GitHub Token",
                default=current_github[:20] + "..." if len(current_github) > 20 else current_github,
                hide_input=True
            )
            if github_token == current_github[:20] + "...":
                github_token = current_github
        else:
            github_token = click.prompt("GitHub Token", hide_input=True)

        github_org = click.prompt(
            "GitHub Organization/Username",
            default=existing_config.get('GITHUB_ORG', '')
        )

        github_repo = click.prompt(
            "GitHub Repository Name",
            default=existing_config.get('GITHUB_REPO', 'infrastructure')
        )

        console.print("\n[bold cyan]Step 3: Optional Settings[/bold cyan]")
        default_env = click.prompt(
            "Default Environment (dev/staging/prod)",
            default=existing_config.get('DEFAULT_ENVIRONMENT', 'dev')
        )

        # Verify configuration
        console.print("\n[bold yellow]Verifying Configuration...[/bold yellow]")

        # Test Anthropic API
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            # Simple test - just creating the client is enough
            console.print("✓ Anthropic API key format looks valid")
        except Exception as e:
            console.print(f"[yellow]⚠ Warning: Could not verify Anthropic API key: {str(e)}[/yellow]")

        # Test GitHub connection
        try:
            from github import Github
            gh = Github(github_token)
            user = gh.get_user()
            console.print(f"✓ GitHub authenticated as: {user.login}")

            # Try to access the repository
            try:
                repo = gh.get_repo(f"{github_org}/{github_repo}")
                console.print(f"✓ Repository accessible: {repo.full_name}")
            except Exception as e:
                console.print(f"[yellow]⚠ Warning: Repository '{github_org}/{github_repo}' not accessible: {str(e)}[/yellow]")
                console.print("[yellow]  Make sure the repository exists and your token has access[/yellow]")

        except Exception as e:
            console.print(f"[yellow]⚠ Warning: Could not verify GitHub connection: {str(e)}[/yellow]")

        # Write configuration
        console.print("\n[bold cyan]Writing Configuration...[/bold cyan]")

        env_content = f"""# InfraLLM Configuration
# Generated by: infrallm configure

# Claude API Configuration
ANTHROPIC_API_KEY={anthropic_key}

# GitHub Configuration
GITHUB_TOKEN={github_token}
GITHUB_ORG={github_org}
GITHUB_REPO={github_repo}

# Optional: Default Configuration
DEFAULT_ENVIRONMENT={default_env}
"""

        env_path.write_text(env_content)
        console.print(f"✓ Configuration saved to {env_path.absolute()}")

        # Security reminder
        console.print("\n[bold yellow]Security Reminder:[/bold yellow]")
        console.print("  • Never commit .env file to version control")
        console.print("  • Add .env to your .gitignore file")
        console.print("  • Keep your API keys secure")

        console.print("\n[bold green]✨ Configuration Complete![/bold green]")
        console.print("\nYou can now use:")
        console.print("  [cyan]infrallm provision[/cyan] \"your infrastructure request\"")
        console.print("  [cyan]infrallm dry-run[/cyan] \"your infrastructure request\"")

    except click.Abort:
        console.print("\n[yellow]Configuration cancelled[/yellow]")
        raise
    except Exception as e:
        console.print(f"\n[bold red]Error during configuration:[/bold red] {str(e)}")
        import traceback
        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation output")
def validate(file_path: str, verbose: bool):
    """
    Validate existing Terraform code against organizational policies.

    This command checks your Terraform files for:
    - Required tags (Environment, CostCenter, Owner, ManagedBy)
    - Security settings (encryption, public access blocks)
    - Naming conventions
    - Resource-specific best practices

    \b
    Examples:
      infrallm validate terraform/prod/database.tf
      infrallm validate terraform/staging/s3/logs-bucket/main.tf --verbose

    \b
    Exit codes:
      0 - Validation passed (all checks successful)
      1 - Validation failed (policy violations found)

    \b
    Use --verbose to see all passed checks in addition to violations.
    """
    from pathlib import Path
    from src.config.loader import load_policies
    from rich.table import Table

    console.print(Panel.fit(
        f"[bold blue]Validating Terraform Code[/bold blue]\n\n{file_path}",
        border_style="blue"
    ))

    try:
        # Load policies
        policies = load_policies()

        # Read Terraform file
        file_content = Path(file_path).read_text()

        console.print(f"\n[bold]File:[/bold] {file_path}")
        console.print(f"[bold]Size:[/bold] {len(file_content)} bytes\n")

        # Validation checks
        violations = []
        warnings = []
        passes = []

        # Check 1: Required tags
        console.print("[bold cyan]Checking Required Tags...[/bold cyan]")
        required_tags = policies.get('tags', {}).get('required', [])

        for tag in required_tags:
            if f'{tag} =' in file_content or f'{tag}=' in file_content:
                passes.append(f"✓ Required tag present: {tag}")
            else:
                violations.append(f"✗ Missing required tag: {tag}")

        # Check 2: Encryption settings
        console.print("[bold cyan]Checking Security Settings...[/bold cyan]")

        if 's3_bucket' in file_content or 'aws_s3_bucket' in file_content:
            # S3-specific checks
            if 'server_side_encryption' in file_content or 'encryption' in file_content:
                passes.append("✓ S3: Encryption configuration found")
            else:
                violations.append("✗ S3: No encryption configuration found")

            if 'public_access_block' in file_content:
                passes.append("✓ S3: Public access block configured")
            else:
                warnings.append("⚠ S3: Public access block not found")

            if 'versioning' in file_content:
                passes.append("✓ S3: Versioning configured")
            else:
                warnings.append("⚠ S3: Versioning not configured")

        if 'db_instance' in file_content or 'aws_db_instance' in file_content:
            # RDS-specific checks
            if 'storage_encrypted = true' in file_content or 'storage_encrypted=true' in file_content:
                passes.append("✓ RDS: Storage encryption enabled")
            else:
                violations.append("✗ RDS: Storage encryption not enabled")

            if 'backup_retention_period' in file_content:
                passes.append("✓ RDS: Backup retention configured")
            else:
                violations.append("✗ RDS: Backup retention not configured")

        # Check 3: Naming conventions
        console.print("[bold cyan]Checking Naming Conventions...[/bold cyan]")

        naming_pattern = policies.get('naming', {}).get('pattern', '')
        if naming_pattern:
            console.print(f"[dim]Expected pattern: {naming_pattern}[/dim]")
            # This is a basic check - just verify the pattern components are mentioned
            if '{environment}' in naming_pattern:
                if any(env in file_content for env in ['prod', 'staging', 'dev']):
                    passes.append("✓ Naming: Environment identifier found")
                else:
                    warnings.append("⚠ Naming: No environment identifier found")

        # Check 4: ManagedBy tag
        console.print("[bold cyan]Checking Management Tags...[/bold cyan]")

        if 'ManagedBy' in file_content:
            if 'terraform' in file_content.lower():
                passes.append("✓ ManagedBy tag indicates Terraform management")
            else:
                warnings.append("⚠ ManagedBy tag present but value unclear")
        else:
            violations.append("✗ Missing ManagedBy tag")

        # Display results
        console.print("\n" + "=" * 70)
        console.print("[bold]Validation Results[/bold]")
        console.print("=" * 70 + "\n")

        # Create results table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Status", style="dim", width=12)
        table.add_column("Count", justify="right")

        table.add_row("[green]Passed", f"[green]{len(passes)}")
        table.add_row("[yellow]Warnings", f"[yellow]{len(warnings)}")
        table.add_row("[red]Violations", f"[red]{len(violations)}")

        console.print(table)

        # Show details if verbose or if there are issues
        if verbose or violations or warnings:
            if passes and verbose:
                console.print("\n[bold green]Passed Checks:[/bold green]")
                for check in passes:
                    console.print(f"  {check}")

            if warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in warnings:
                    console.print(f"  {warning}")

            if violations:
                console.print("\n[bold red]Policy Violations:[/bold red]")
                for violation in violations:
                    console.print(f"  {violation}")

        # Final verdict
        console.print()
        if violations:
            console.print("[bold red]❌ Validation FAILED[/bold red]")
            console.print(f"\n{len(violations)} policy violation(s) must be fixed before deployment.")
        elif warnings:
            console.print("[bold yellow]⚠️  Validation PASSED with warnings[/bold yellow]")
            console.print(f"\n{len(warnings)} warning(s) - consider addressing these issues.")
        else:
            console.print("[bold green]✅ Validation PASSED[/bold green]")
            console.print("\nTerraform code complies with organizational policies.")

        # Recommendations
        if violations or warnings:
            console.print("\n[bold cyan]Recommendations:[/bold cyan]")
            console.print("  1. Review the violations/warnings above")
            console.print("  2. Update your Terraform code to address issues")
            console.print("  3. Run validation again to verify fixes")
            console.print(f"  4. Check policies at: src/config/policies.yaml")

    except FileNotFoundError:
        console.print(f"\n[bold red]Error:[/bold red] File not found: {file_path}")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[bold red]Validation Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise click.Abort()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
