"""
RBAC (Role-Based Access Control) — Phase 5 Security Hardening
=============================================================
Provides role-hierarchy enforcement for HDIP endpoints.

Roles (ascending privilege):
  analyst   → Read-only access to analytics, predictions, dashboards
  clinician → analyst + patient risk assessments
  manager   → clinician + alert acknowledgement, decision acceptance
  executive → manager + all decision actions, scenario simulation
  admin     → Full system access including user management

Usage in route:
  @router.post("/simulate")
  async def run_simulation(
      payload: dict,
      current_user: User = Depends(require_roles("executive", "admin"))
  ):
"""

from functools import lru_cache
from typing import List
from fastapi import Depends, HTTPException, status
from app.core.permissions import get_current_user
from app.models.user import User, UserRole

# Role hierarchy — higher index = more privilege
ROLE_HIERARCHY: List[str] = [
    UserRole.ANALYST,
    UserRole.CLINICIAN,
    UserRole.MANAGER,
    UserRole.EXECUTIVE,
    UserRole.ADMIN,
]

def _role_level(role: str) -> int:
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError:
        return -1


def require_roles(*allowed_roles: str):
    """
    FastAPI dependency factory that checks if the current user
    holds any of the allowed roles (or a higher-privilege role).

    Usage:
        current_user: User = Depends(require_roles("manager", "executive", "admin"))
    """
    min_level = min(_role_level(r) for r in allowed_roles)

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        user_level = _role_level(current_user.role)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient privileges. "
                    f"Required role(s): {list(allowed_roles)}. "
                    f"Current role: {current_user.role}."
                ),
            )
        return current_user

    return _check
