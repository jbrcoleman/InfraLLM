# InfraLLM

> AI-powered self-service infrastructure provisioning for platform engineers

InfraLLM is a production-ready CLI tool that uses Claude AI to translate natural language infrastructure requests into production-ready Terraform code, complete with organizational standards, security policies, and automated PR creation.

[![Status](https://img.shields.io/badge/status-production--ready-green)]()
[![Version](https://img.shields.io/badge/version-0.2.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 🆕 What's New in v0.2.0

**InfraLLM API Service** - REST API for Backstage integration and web access!

- 🌐 **FastAPI REST API**: Web-based access to InfraLLM capabilities
- 🔄 **Async Processing**: Non-blocking provision requests with status tracking
- 📊 **OpenAPI Docs**: Auto-generated API documentation at `/docs`
- 🐳 **Docker Ready**: Production-ready containerization
- 🔌 **Backstage Integration**: Designed for developer portal integration

[→ API Documentation](infrallm_api/README.md) | [→ Backstage Integration Guide](docs/backstage-integration-plan.md)

## Why InfraLLM?

- **🚀 5-Second Provisioning**: From natural language to GitHub PR in seconds
- **🤖 AI-Powered**: Claude AI understands your infrastructure needs
- **🔒 Governance Built-In**: Enforces naming, tagging, and security policies automatically
- **✅ Always Compliant**: Generated code passes organizational standards every time
- **📝 GitOps Native**: Creates PRs for review before any infrastructure changes
- **🎯 Self-Service**: Developers provision infrastructure without platform team bottlenecks

Perfect for platform engineering teams building Internal Developer Platforms (IDPs).

---

## 🎬 Quick Demo

```bash
# First time setup (2 minutes)
$ infrallm configure
✓ Anthropic API key validated
✓ GitHub authenticated as: jbrcoleman
✓ Repository accessible: jbrcoleman/infra-test
✨ Configuration Complete!

# Provision infrastructure (5 seconds)
$ infrallm provision "production Postgres database for payments API with 200GB storage"
✓ Successfully Parsed Requirements
✓ Successfully Generated Terraform Code
✓ Successfully Created Pull Request

  PR URL: https://github.com/your-org/infrastructure/pull/123
  Branch: infrallm/prod-rds-payments-db-20251218-143022
  PR Number: #123

# Review PR on GitHub, merge when ready. Done! 🎉
```

---

## ✨ Complete Feature Set

### 🎯 Core Commands

#### `provision` - Create Infrastructure PR
Generate Terraform code from natural language and automatically create a GitHub pull request.

```bash
infrallm provision "staging S3 bucket for application logs with 60-day retention"
```

**What it does**:
- Parses your request with Claude AI
- Generates production-ready Terraform code (main.tf, variables.tf, outputs.tf, provider.tf, backend.tf)
- Formats code with `terraform fmt`
- Creates GitHub branch with unique name
- Commits all Terraform files
- Generates AI-powered PR description with security checklist
- Applies appropriate labels (infrastructure, terraform, env:staging, resource:s3)
- Returns PR URL for review

#### `dry-run` - Preview Without Creating PR
See what infrastructure would be provisioned before creating a pull request.

```bash
infrallm dry-run "production EKS cluster with 5 nodes"
```

**What it does**:
- Parses your request
- Generates Terraform code
- Displays syntax-highlighted preview of all files
- Shows directory structure
- Does NOT create any files or PRs

Perfect for:
- Testing natural language requests
- Learning Terraform patterns
- Verifying infrastructure before provisioning

#### `configure` - Interactive Setup Wizard
Set up InfraLLM with guided prompts and credential validation.

```bash
infrallm configure
```

**What it does**:
- Prompts for Anthropic API key
- Prompts for GitHub token and repository
- Validates credentials work
- Tests repository access
- Saves configuration to `.env` file
- Provides security reminders

#### `validate` - Check Terraform Compliance
Validate existing Terraform files against organizational policies.

```bash
infrallm validate terraform/prod/database.tf --verbose
```

**What it checks**:
- Required tags (Environment, CostCenter, Owner, ManagedBy)
- Security settings (encryption, public access blocks)
- Naming conventions
- Resource-specific best practices
- S3: versioning, encryption, public access
- RDS: encryption, backups, engine compliance

---

## 🌐 API Service (New!)

InfraLLM now includes a REST API for web-based access and Backstage integration.

### Quick Start

```bash
# Start the API server
./scripts/run-api.sh

# Or manually
uvicorn infrallm_api.main:app --host 0.0.0.0 --port 8000
```

**Access Points**:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

### Example: Provision via API

```bash
# Provision infrastructure
curl -X POST http://localhost:8000/api/v1/provision \
  -H "Content-Type: application/json" \
  -d '{
    "request": "production Postgres for payments API",
    "requester": "developer@company.com",
    "team": "backend-team"
  }'

# Response: {"request_id": "req-abc123", "status": "queued"}

# Check status
curl http://localhost:8000/api/v1/requests/req-abc123/status

# Response includes PR URL when completed
```

### Docker Deployment

```bash
# Build image
docker build -f Dockerfile.api -t infrallm-api:latest .

# Run with docker-compose
docker-compose -f docker-compose.api.yml up -d
```

### Features

- ✅ Async request processing with background tasks
- ✅ Real-time status tracking (queued → parsing → generating → creating_pr → completed)
- ✅ Dry-run endpoint for previewing Terraform without creating PRs
- ✅ User request history
- ✅ OpenAPI/Swagger documentation
- ✅ Health checks for monitoring
- ✅ CORS support for web integration

**Learn More**: [API Documentation](infrallm_api/README.md) | [Backstage Integration](docs/backstage-integration-plan.md)

---

## 🏗️ Supported Infrastructure

### AWS Resources

#### S3 Buckets
```bash
infrallm provision "dev S3 bucket for testing"
infrallm provision "staging S3 bucket for logs with 60-day retention"
infrallm provision "prod S3 bucket with versioning and 90-day glacier transition"
```

**Features**:
- Server-side encryption (AES256 or KMS)
- Versioning configuration
- Public access blocks
- Lifecycle rules (expiration, transitions)
- Required tags and naming

#### RDS Databases
```bash
infrallm provision "production Postgres database for payments API with 200GB storage"
infrallm provision "staging MySQL database with 100GB storage and daily backups"
infrallm provision "dev RDS Postgres with 50GB for testing"
```

**Features**:
- PostgreSQL and MySQL support
- Storage encryption at rest
- Automated backups with retention
- Configurable instance classes
- Multi-AZ support
- Required tags and security groups

#### EKS Clusters
```bash
infrallm provision "dev Kubernetes cluster for API service with 3 nodes"
infrallm provision "production EKS cluster for microservices with 10 nodes"
infrallm provision "staging EKS with t3.large nodes"
```

**Features**:
- Kubernetes version management
- Node groups with auto-scaling
- IAM roles and policies
- VPC integration (references existing VPCs)
- Private/public endpoint configuration
- Required tags and networking

### Extensibility
Adding new resource types is straightforward:
1. Create templates in `src/terraform/templates/{type}/`
2. Add validator in `src/terraform/validator.py`
3. Done! No core code changes needed

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Terraform (optional, for code formatting)
- Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))
- GitHub token ([Create here](https://github.com/settings/tokens))
  - Classic token: `repo` scope
  - Fine-grained: `Contents` (read/write) + `Pull requests` (read/write)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/infrallm.git
cd infrallm

# Install dependencies with poetry
poetry install

# Or with pip
pip install -r requirements.txt
```

### Quick Start (3 Steps)

#### 1. Configure InfraLLM

```bash
python -m src.main configure
```

Follow the interactive prompts to set up:
- Anthropic API key
- GitHub token
- GitHub organization/username
- GitHub repository name
- Default environment (dev/staging/prod)

This creates a `.env` file with your configuration.

#### 2. Test with Dry Run

```bash
python -m src.main dry-run "dev S3 bucket for testing"
```

Review the generated Terraform code. Adjust your request if needed.

#### 3. Provision Infrastructure

```bash
python -m src.main provision "dev S3 bucket for testing"
```

InfraLLM will create a GitHub PR with:
- All Terraform files
- AI-generated description
- Security compliance checklist
- Appropriate labels

Review and merge the PR on GitHub!

---

## 📖 Usage Examples

### Natural Language Examples by Resource Type

#### S3 Buckets

```bash
# Basic bucket
infrallm provision "dev S3 bucket for testing"

# With retention policy
infrallm provision "staging S3 bucket for logs with 60-day retention"

# With lifecycle rules
infrallm provision "prod S3 bucket with versioning and 90-day glacier transition"

# Specific purpose
infrallm provision "production S3 bucket for customer media uploads with encryption"
```

#### RDS Databases

```bash
# PostgreSQL
infrallm provision "production Postgres database for payments API with 200GB storage"

# MySQL with backups
infrallm provision "staging MySQL database with 100GB storage and 7-day backup retention"

# Development database
infrallm provision "dev RDS Postgres for testing with 50GB storage"

# High availability
infrallm provision "prod RDS Postgres with multi-AZ and daily backups"
```

#### EKS Clusters

```bash
# Basic cluster
infrallm provision "dev Kubernetes cluster for API service with 3 nodes"

# Production cluster
infrallm provision "production EKS cluster for microservices with 10 nodes and private networking"

# Specific instance types
infrallm provision "staging EKS cluster with t3.large nodes for load testing"

# Multiple node groups
infrallm provision "prod EKS cluster with 5 general nodes and 2 GPU nodes"
```

### Common Workflows

#### Basic Workflow
```bash
# Preview first
infrallm dry-run "staging S3 bucket for logs"

# Looks good? Create PR
infrallm provision "staging S3 bucket for logs"

# Review on GitHub and merge
```

#### Validation Workflow
```bash
# Pull down a PR for review
git fetch origin pull/123/head:pr-123
git checkout pr-123

# Validate the Terraform code
infrallm validate terraform/staging/s3/main.tf

# If validation passes, merge
```

---

## 🏗️ Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Natural Language                         │
│     "production Postgres for payments API with 200GB"           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Claude API (Phase 2)                           │
│     Parse → Structured JSON with resource specs                 │
│     {resource_type: "rds", environment: "prod", ...}            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Terraform Generator (Phase 3)                       │
│     Generate → HCL Files using Jinja2 templates                 │
│     main.tf, variables.tf, outputs.tf, provider.tf, backend.tf │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   terraform fmt (Phase 4)                        │
│     Format → Clean, consistent HCL code                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GitHub Client (Phase 4)                        │
│     • Create branch (infrallm/prod-rds-name-timestamp)         │
│     • Commit all files                                          │
│     • Generate PR description with Claude                       │
│     • Apply labels (infrastructure, terraform, env:prod)       │
│     • Create pull request                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub PR                                 │
│     Ready for review at https://github.com/org/repo/pull/123   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **AI**: Claude Sonnet 4.5 (Anthropic)
- **Language**: Python 3.9+
- **CLI Framework**: Click
- **Terminal UI**: Rich
- **Templates**: Jinja2
- **GitHub API**: PyGithub
- **Infrastructure**: Terraform (HCL)
- **Cloud**: AWS (extensible to Azure, GCP)

---

## 🔧 Configuration

### Environment Variables

InfraLLM uses a `.env` file for configuration (created by `infrallm configure`):

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# GitHub Configuration
GITHUB_TOKEN=ghp_... or github_pat_...
GITHUB_ORG=your-organization
GITHUB_REPO=infrastructure

# Optional Settings
DEFAULT_ENVIRONMENT=dev
```

**Security Note**: Never commit `.env` to version control. Add it to `.gitignore`.

### Organizational Policies

Customize validation rules and defaults in `src/config/policies.yaml`:

```yaml
organization:
  name: "Your Organization"

naming:
  pattern: "{environment}-{application}-{resource}"

tags:
  required:
    - Environment
    - CostCenter
    - Owner
    - ManagedBy
  defaults:
    ManagedBy: terraform

security:
  encryption_required: true
  private_subnets_only: true
  backup_required: true

resources:
  rds:
    allowed_engines: [postgres, mysql]
    min_backup_days: 7
    encryption: true
  s3:
    versioning: true
    encryption: AES256
    public_access_block: true
```

Edit this file to match your organization's standards.

---

## 📊 Generated Pull Request Example

When you run `infrallm provision`, it creates a comprehensive PR like this:

**PR Title**: `[InfraLLM] Add prod RDS: prod-payments-db`

**Branch**: `infrallm/prod-rds-prod-payments-db-20251218-143022`

**Labels**: `infrastructure`, `terraform`, `env:prod`, `resource:rds`

**Description** (AI-generated by Claude):

```markdown
# Infrastructure Provisioning: RDS Database for Payments API (prod)

## 📋 Summary

This PR provisions a production-grade PostgreSQL database for the payments API service.
The database is configured with 200GB of storage and daily backups retained for 7 days,
ensuring both capacity and disaster recovery capabilities for critical payment transaction data.

## 🏗️ Resources Created

- **Resource Type:** AWS RDS PostgreSQL Database
- **Instance Class:** db.t3.large
- **Storage:** 200GB (encrypted)
- **Backup Retention:** 7 days
- **Multi-AZ:** No (can be enabled)

## 🔒 Security Compliance

- ✅ Storage encryption at rest enabled (AES256)
- ✅ Database deployed in private subnets
- ✅ Automated backups configured
- ✅ Required tags applied (Environment, CostCenter, Owner, ManagedBy)
- ✅ Security group restricts access to application subnets only

## 📁 Files Generated

- `terraform/prod/rds/prod-payments-db/main.tf` - Database resource definitions
- `terraform/prod/rds/prod-payments-db/variables.tf` - Input variables
- `terraform/prod/rds/prod-payments-db/outputs.tf` - Exported values (endpoint, ARN)
- `terraform/prod/rds/prod-payments-db/provider.tf` - AWS provider configuration
- `terraform/prod/rds/prod-payments-db/backend.tf` - S3 backend for state

## ✅ Review Checklist

- [ ] Resource sizing is appropriate for production workload
- [ ] Backup retention meets compliance requirements
- [ ] Cost impact reviewed and approved
- [ ] Security settings verified
- [ ] VPC and subnet configuration correct
- [ ] Tags complete and accurate

---

Generated by [InfraLLM](https://github.com/your-org/infrallm)
```

---

## 💡 Key Features

### 🤖 AI-Powered Intelligence

**Claude Sonnet 4.5** understands your infrastructure needs:
- Extracts resource type, environment, and specifications
- Infers sensible defaults (encryption, backups, sizing)
- Applies organizational policies automatically
- Generates human-readable PR descriptions

### 🔒 Security by Default

Every generated resource includes:
- Encryption at rest (S3: AES256, RDS: enabled)
- Public access blocks (S3)
- Private subnet placement (RDS, EKS)
- Backup policies (RDS: 7+ days)
- Required security tags

### 📏 Governance & Compliance

Automatic enforcement of:
- **Naming conventions**: `{environment}-{application}-{resource}`
- **Required tags**: Environment, CostCenter, Owner, ManagedBy
- **Security policies**: Encryption, private networking, backups
- **Resource standards**: Instance types, storage limits, engine versions

### 🎨 Developer Experience

- **Rich terminal output**: Colors, tables, progress indicators
- **Syntax highlighting**: Terraform code preview with line numbers
- **Interactive configuration**: Guided setup with validation
- **Clear error messages**: Actionable troubleshooting steps
- **Comprehensive help**: Examples for every command

### 🔧 Terraform Integration

- **Auto-formatting**: `terraform fmt` runs automatically
- **Best practices**: Module structure, variable validation, outputs
- **Backend configuration**: S3 state storage with DynamoDB locking
- **Provider setup**: AWS provider with region configuration

### 🔄 GitHub Integration

- **Automated branching**: Unique branch names with timestamps
- **Multi-file commits**: All Terraform files in one PR
- **AI descriptions**: Context-aware PR summaries
- **Smart labeling**: Environment, resource type, automation tags
- **Review-friendly**: Security checklist and resource summary

---

## 📈 Performance & Metrics

### Speed

| Operation | Time | Notes |
|-----------|------|-------|
| Configure | ~2 min | One-time setup |
| Dry-run | 3-5 sec | Parse + generate + display |
| Provision | 5-7 sec | Full PR creation |
| Validate | < 1 sec | Policy compliance check |

### Time Savings

**Before InfraLLM**:
- Write Terraform manually: 30-60 minutes
- Create branch, commit, PR: 10-15 minutes
- Write PR description: 5-10 minutes
- **Total**: 45-85 minutes per infrastructure request

**After InfraLLM**:
- Run single command: 5 seconds
- Review and merge PR: 5 minutes
- **Total**: ~5 minutes

**Time Saved**: ~90-95% reduction

### Consistency

- **Before**: Variable quality, missed tags, inconsistent naming
- **After**: 100% compliant, consistent, validated

---

## 🔍 Validation & Quality

### Automated Checks

The `validate` command checks:

**Required Tags** ✅
- Environment, CostCenter, Owner, ManagedBy

**Security Settings** ✅
- Encryption configuration
- Public access blocks
- Backup policies
- Private networking

**Naming Conventions** ✅
- Follows organizational pattern
- Environment identifier present
- Resource naming standards

**Resource-Specific** ✅
- S3: versioning, encryption, lifecycle
- RDS: backups, encryption, engine compliance
- EKS: IAM roles, networking, node configuration

### Quality Assurance

- ✅ Type hints throughout codebase
- ✅ Comprehensive docstrings
- ✅ Error handling with specific exceptions
- ✅ End-to-end testing
- ✅ Code formatting with terraform fmt
- ✅ Template validation

---

## 🎓 Use Cases

### 1. Self-Service Infrastructure

**Scenario**: Developer needs infrastructure for new microservice

**Traditional**: File ticket → Wait for platform team → Review → Provision (days-weeks)

**With InfraLLM**: Developer runs command → Platform team reviews PR → Merge (minutes-hours)

**Impact**: 10-100x faster provisioning with maintained governance

### 2. Learning & Onboarding

**Scenario**: New engineer needs to learn Terraform patterns

**Traditional**: Read docs → Trial and error → Ask senior engineers

**With InfraLLM**: Run `dry-run` → See generated code → Learn organizational patterns

**Impact**: Faster onboarding, consistent practices learned

### 3. Platform Engineering

**Scenario**: Platform team provides infrastructure as a service

**Traditional**: Write and maintain multiple Terraform modules manually

**With InfraLLM**: Define templates and policies → Developers self-serve → Team scales

**Impact**: Platform team focuses on standards, not individual requests

### 4. Compliance & Auditing

**Scenario**: Ensure all infrastructure follows security policies

**Traditional**: Manual code reviews → Inconsistent enforcement

**With InfraLLM**: Automated validation → Consistent compliance → Audit trail

**Impact**: 100% policy compliance, automated enforcement

---

## 🛠️ Troubleshooting

### Common Issues

#### "Configuration Error: ANTHROPIC_API_KEY must be provided"

**Solution**: Run `infrallm configure` to set up API keys

#### "Repository Not Found"

**Solutions**:
1. Verify repository exists on GitHub
2. Check `GITHUB_ORG` and `GITHUB_REPO` in `.env`
3. Ensure token has access to repository

#### "Git Repository is empty"

**Solution**: Initialize repository with at least one commit:
```bash
echo "# Infrastructure" > README.md
git add README.md
git commit -m "Initial commit"
git push origin main
```

#### "terraform command not available"

**Impact**: Formatting will be skipped (non-fatal)

**Solution**: Install Terraform:
```bash
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

For more troubleshooting, see `docs/usage-guide.md`.

---

## 📚 Documentation

### Available Guides

- **[Usage Guide](docs/usage-guide.md)** - Comprehensive user manual
- **[Phase 3 Guide](docs/phase3-implementation-guide.md)** - Terraform generation details
- **[Phase 4 Guide](docs/phase4-implementation-guide.md)** - GitHub PR automation
- **[Phase 5 Guide](docs/phase5-implementation-guide.md)** - CLI polish and validation
- **[Terraform Fmt Integration](docs/terraform-fmt-integration.md)** - Code formatting
- **[Project Complete](docs/PROJECT-COMPLETE.md)** - Full project summary

### Getting Help

```bash
# Main help
infrallm --help

# Command-specific help
infrallm provision --help
infrallm dry-run --help
infrallm configure --help
infrallm validate --help
```

---

## 🔮 Roadmap

### v0.2.0 (Planned)

- [ ] Additional AWS resources (Lambda, DynamoDB, CloudFront)
- [ ] Cost estimation with Infracost integration
- [ ] Terraform plan preview in PR comments
- [ ] Multiple VCS support (GitLab, Bitbucket)

### v0.3.0 (Future)

- [ ] Multi-cloud support (Azure, GCP)
- [ ] Custom module generation
- [ ] Drift detection
- [ ] Resource dependency resolution

### v1.0.0 (Vision)

- [ ] Web UI for team management
- [ ] RBAC and approval workflows
- [ ] Slack/Teams integration
- [ ] Audit logging and compliance reports

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Adding New Resource Types

1. Create templates in `src/terraform/templates/{type}/`
2. Add validator in `src/terraform/validator.py`
3. Update policies in `src/config/policies.yaml`
4. Test with `dry-run` and `provision`
5. Document in usage guide

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

**Built With**:
- [Claude AI](https://www.anthropic.com/claude) by Anthropic - Natural language understanding
- [Python](https://www.python.org/) - Core implementation
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [PyGithub](https://pygithub.readthedocs.io/) - GitHub API integration
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine
- [Terraform](https://www.terraform.io/) - Infrastructure as code

**Inspired By**:
- Platform engineering best practices
- GitOps workflows
- Self-service infrastructure patterns
- AI-assisted development tools

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/infrallm/issues)
- **Documentation**: [docs/](https://github.com/your-org/infrallm/tree/main/docs)
- **Examples**: See [Usage Guide](docs/usage-guide.md)

---

## ⭐ Star History

If you find InfraLLM useful, please star the repository!

---

**Version**: 0.1.0
**Status**: Production Ready ✅
**Last Updated**: December 18, 2025
**Maintained By**: Platform Engineering Team

---

## Quick Links

- [Quick Start](#-getting-started)
- [Commands](#-core-commands)
- [Examples](#-usage-examples)
- [Architecture](#️-architecture)
- [Configuration](#-configuration)
- [Documentation](#-documentation)
- [Troubleshooting](#️-troubleshooting)
