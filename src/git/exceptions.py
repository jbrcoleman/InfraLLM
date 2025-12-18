"""
GitHub integration exceptions.

Custom exceptions for GitHub operations like PR creation, branch management, etc.
"""


class GitHubError(Exception):
    """Base exception for GitHub-related errors."""
    pass


class ConfigurationError(GitHubError):
    """Raised when GitHub configuration is missing or invalid."""
    pass


class BranchCreationError(GitHubError):
    """Raised when branch creation fails."""
    pass


class CommitError(GitHubError):
    """Raised when commit operation fails."""
    pass


class PullRequestError(GitHubError):
    """Raised when pull request creation fails."""
    pass


class RepositoryNotFoundError(GitHubError):
    """Raised when the specified repository cannot be found."""
    pass
