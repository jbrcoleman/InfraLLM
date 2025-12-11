# InfraLLM

> AI-powered self-service infrastructure provisioning for platform engineers

InfraLLM is a CLI tool that uses Claude AI to translate natural language infrastructure requests into production-ready Terraform code, complete with organizational standards, security policies, and automated PR creation.

## Project Status

**Phase 1: COMPLETED** - Core project structure and CLI framework

- Python CLI project with Click framework
- Poetry dependency management configured
- Complete directory structure
- Basic CLI commands (provision, dry-run, configure, validate)

**Upcoming Phases:**
- Phase 2: Claude API integration for natural language parsing
- Phase 3: Terraform code generation
- Phase 4: GitHub PR automation
- Phase 5: CLI polish and advanced features

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or Poetry for dependency management

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd InfraLLM
```

2. Install dependencies:
```bash
# Using pip
pip install anthropic PyGithub click pyyaml rich

# Or using Poetry
poetry install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### CLI Commands

```bash
# View help
python -m src.main --help

# Provision infrastructure (Phase 2+)
python -m src.main provision "I need a production Postgres database for the payments API"

# Dry run mode (Phase 3+)
python -m src.main dry-run "staging S3 bucket for log aggregation"

# Configure settings (Phase 5+)
python -m src.main configure

# Validate existing Terraform (Phase 5+)
python -m src.main validate terraform/prod/database.tf
```

## Project Structure

```
infrallm/
├── README.md
├── PLAN.md                 # Detailed implementation plan
├── pyproject.toml          # Poetry configuration and dependencies
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore patterns
├── src/
│   ├── __init__.py
│   ├── main.py            # CLI entry point (Click framework)
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py      # Claude API wrapper (Phase 2)
│   ├── terraform/
│   │   ├── __init__.py
│   │   ├── generator.py   # Terraform code generation (Phase 3)
│   │   └── templates/     # Base templates for common resources
│   ├── git/
│   │   ├── __init__.py
│   │   └── github.py      # GitHub PR creation (Phase 4)
│   └── config/
│       ├── __init__.py
│       └── policies.yaml  # Org standards, naming conventions
└── tests/
```

## Configuration

### Environment Variables

Required environment variables (see `.env.example`):

```bash
# Claude API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_ORG=your-organization-name
GITHUB_REPO=infrastructure
```

### Organizational Policies

Edit `src/config/policies.yaml` to customize:

- Naming conventions
- Required tags
- Security policies
- Resource-specific defaults

## Features (Planned)

- Natural language parsing with Claude AI
- Terraform code generation with organizational standards
- Automated GitHub PR creation
- Policy enforcement (naming, tagging, security)
- Dry-run mode for previewing changes
- Rich terminal output with colors and progress indicators
- Validation of existing Terraform code

## Development

### Running Tests

```bash
# Tests will be added in future phases
pytest tests/
```

### Code Formatting

```bash
# Format code with black
black src/

# Lint with ruff
ruff check src/
```

## Next Steps

To continue development, follow the phases outlined in PLAN.md:

1. **Phase 2**: Implement Claude API client for parsing natural language requests
2. **Phase 3**: Build Terraform code generator with templates
3. **Phase 4**: Add GitHub integration for automated PR creation
4. **Phase 5**: Polish CLI with rich output and additional features

See `PLAN.md` for detailed implementation instructions for each phase.

## License

MIT

## Contributing

This project is designed to be extensible. Add new resource types, cloud providers, or integrations by following the existing patterns.

---

Built for platform engineers who want to combine the power of AI with the safety of GitOps.