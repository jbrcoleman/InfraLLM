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
@click.version_option(version="0.1.0")
def cli():
    """
    InfraLLM - AI-powered self-service infrastructure provisioning.

    Use natural language to generate production-ready Terraform code
    with organizational standards and automated PR creation.
    """
    pass


@cli.command()
@click.argument("request", type=str)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def provision(request: str, verbose: bool):
    """
    Generate Terraform code from natural language and create a GitHub PR.

    Example:
        infrallm provision "I need a production Postgres database for the payments API"
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

        # TODO: Phase 4 - Create GitHub PR with terraform files
        console.print("\n[yellow]⚠ GitHub PR creation will be implemented in Phase 4[/yellow]")

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

    Example:
        infrallm dry-run "staging S3 bucket for log aggregation"
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
    Interactive setup for API keys and organizational policies.

    This command will guide you through setting up:
    - Anthropic API key
    - GitHub token and repository settings
    - Organizational policies and standards
    """
    console.print(Panel.fit(
        "[bold green]InfraLLM Configuration[/bold green]",
        border_style="green"
    ))

    try:
        # TODO: Phase 5 - Implement interactive configuration
        console.print("[yellow]⚠ This feature will be implemented in Phase 5[/yellow]")

        # Placeholder workflow:
        # 1. Prompt for ANTHROPIC_API_KEY
        # 2. Prompt for GITHUB_TOKEN
        # 3. Prompt for GitHub org/repo
        # 4. Create/update .env file
        # 5. Optionally configure policies.yaml

        console.print("\n[dim]For now, please manually create a .env file based on .env.example[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def validate(file_path: str):
    """
    Validate existing Terraform code against organizational policies.

    Example:
        infrallm validate terraform/prod/database.tf
    """
    console.print(Panel.fit(
        f"[bold blue]Validating Terraform Code[/bold blue]\n\n{file_path}",
        border_style="blue"
    ))

    try:
        # TODO: Phase 5 - Implement validation logic
        console.print("[yellow]⚠ This feature will be implemented in Phase 5[/yellow]")

        # Placeholder workflow:
        # 1. Read Terraform file
        # 2. Check naming conventions
        # 3. Verify required tags
        # 4. Validate security settings
        # 5. Report compliance status

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
