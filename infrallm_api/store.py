"""
In-memory store for tracking provision requests.

In production, this should be replaced with Redis or PostgreSQL.
"""

from datetime import datetime
from typing import Dict, Optional
from .models.requests import RequestStatus, StatusResponse


class RequestStore:
    """In-memory storage for provision requests."""

    def __init__(self):
        self._store: Dict[str, dict] = {}

    def create(
        self,
        request_id: str,
        request_text: str,
        requester: str,
        team: Optional[str] = None,
        service: Optional[str] = None,
    ) -> None:
        """Create a new request entry."""
        self._store[request_id] = {
            "request_id": request_id,
            "request_text": request_text,
            "requester": requester,
            "team": team,
            "service": service,
            "status": RequestStatus.QUEUED,
            "created_at": datetime.utcnow(),
            "pr_url": None,
            "pr_number": None,
            "branch_name": None,
            "error": None,
            "requirements": None,
            "completed_at": None,
        }

    def update(self, request_id: str, **fields) -> None:
        """Update request fields."""
        if request_id not in self._store:
            raise KeyError(f"Request {request_id} not found")
        self._store[request_id].update(fields)

    def get(self, request_id: str) -> Optional[dict]:
        """Get request by ID."""
        return self._store.get(request_id)

    def get_status_response(self, request_id: str) -> Optional[StatusResponse]:
        """Get request as StatusResponse model."""
        data = self.get(request_id)
        if data is None:
            return None
        return StatusResponse(**data)

    def list_by_user(self, requester: str, limit: int = 20) -> list[dict]:
        """List requests by user."""
        user_requests = [
            req for req in self._store.values()
            if req["requester"] == requester
        ]
        # Sort by created_at descending
        user_requests.sort(key=lambda x: x["created_at"], reverse=True)
        return user_requests[:limit]

    def exists(self, request_id: str) -> bool:
        """Check if request exists."""
        return request_id in self._store


# Global instance (in production, use dependency injection)
request_store = RequestStore()
