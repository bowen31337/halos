"""Role-based access control (RBAC) utilities and dependencies.

This module provides decorators and FastAPI dependencies for enforcing
role-based permissions on API endpoints.
"""

from enum import Enum
from typing import Set, Optional, List, Union
from functools import wraps

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.session import TokenData, JWTBearer, session_manager
from src.core.database import get_db
from src.models.user import User


class Role(str, Enum):
    """User roles with increasing privilege levels."""

    USER = "user"           # Basic user - can use chat, create conversations
    ADMIN = "admin"         # Admin - can manage users, projects, view audit logs
    SUPERUSER = "superuser" # Superuser - full system access


class Permission(str, Enum):
    """Granular permissions that can be assigned to roles or users."""

    # Conversation permissions
    CONVERSATION_CREATE = "conversation:create"
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_UPDATE = "conversation:update"
    CONVERSATION_DELETE = "conversation:delete"
    CONVERSATION_EXPORT = "conversation:export"
    CONVERSATION_SHARE = "conversation:share"

    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_FILES = "project:manage_files"

    # User management permissions
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    # System permissions
    VIEW_AUDIT_LOGS = "system:view_audit_logs"
    VIEW_ANALYTICS = "system:view_analytics"
    MANAGE_SYSTEM = "system:manage"
    MANAGE_MCP_SERVERS = "system:manage_mcp"

    # Memory permissions
    MEMORY_CREATE = "memory:create"
    MEMORY_READ = "memory:read"
    MEMORY_UPDATE = "memory:update"
    MEMORY_DELETE = "memory:delete"

    # Prompt library permissions
    PROMPT_CREATE = "prompt:create"
    PROMPT_READ = "prompt:read"
    PROMPT_UPDATE = "prompt:update"
    PROMPT_DELETE = "prompt:delete"

    # Template permissions
    TEMPLATE_CREATE = "template:create"
    TEMPLATE_READ = "template:read"
    TEMPLATE_UPDATE = "template:update"
    TEMPLATE_DELETE = "template:delete"

    # Collaboration permissions
    COLLABORATION_JOIN = "collaboration:join"
    COLLABORATION_MANAGE = "collaboration:manage"


# Role-to-permission mappings
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.USER: {
        # Basic conversation operations
        Permission.CONVERSATION_CREATE,
        Permission.CONVERSATION_READ,
        Permission.CONVERSATION_UPDATE,
        Permission.CONVERSATION_DELETE,
        Permission.CONVERSATION_EXPORT,
        Permission.CONVERSATION_SHARE,

        # Project operations (own projects)
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_MANAGE_FILES,

        # Memory operations
        Permission.MEMORY_CREATE,
        Permission.MEMORY_READ,
        Permission.MEMORY_UPDATE,
        Permission.MEMORY_DELETE,

        # Prompt operations
        Permission.PROMPT_CREATE,
        Permission.PROMPT_READ,
        Permission.PROMPT_UPDATE,
        Permission.PROMPT_DELETE,

        # Template operations
        Permission.TEMPLATE_CREATE,
        Permission.TEMPLATE_READ,
        Permission.TEMPLATE_UPDATE,
        Permission.TEMPLATE_DELETE,

        # Collaboration
        Permission.COLLABORATION_JOIN,
    },

    Role.ADMIN: ROLE_PERMISSIONS[Role.USER] | {
        # User management (except role management)
        Permission.USER_READ,
        Permission.USER_UPDATE,

        # System permissions
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_ANALYTICS,

        # Project management (all projects)
        Permission.PROJECT_DELETE,

        # MCP server management
        Permission.MANAGE_MCP_SERVERS,

        # Collaboration management
        Permission.COLLABORATION_MANAGE,
    },

    Role.SUPERUSER: ROLE_PERMISSIONS[Role.ADMIN] | {
        # Full user management
        Permission.USER_DELETE,
        Permission.USER_MANAGE_ROLES,

        # Full system access
        Permission.MANAGE_SYSTEM,
    },
}


def get_user_role_permissions(role: Union[str, Role], include_custom: Optional[Set[Permission]] = None) -> Set[Permission]:
    """Get all permissions for a role, optionally including custom permissions.

    Args:
        role: The role to get permissions for
        include_custom: Additional custom permissions to include

    Returns:
        Set of permissions
    """
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return set()

    permissions = ROLE_PERMISSIONS.get(role, set()).copy()

    if include_custom:
        permissions.update(include_custom)

    return permissions


def has_permission(user_permissions: Set[Permission], required: Permission) -> bool:
    """Check if user has required permission."""
    return required in user_permissions


def has_any_permission(user_permissions: Set[Permission], *required: Permission) -> bool:
    """Check if user has any of the required permissions."""
    return any(p in user_permissions for p in required)


class PermissionChecker:
    """FastAPI dependency for checking permissions."""

    def __init__(self, required_permissions: Union[Permission, List[Permission]]):
        """Initialize with required permission(s).

        Args:
            required_permissions: Single permission or list of permissions
        """
        if isinstance(required_permissions, Permission):
            self.required = {required_permissions}
        else:
            self.required = set(required_permissions)

    async def __call__(
        self,
        token_data: TokenData = Depends(JWTBearer()),
        db: AsyncSession = Depends(get_db),
    ) -> TokenData:
        """Check if user has required permissions."""
        # Get user from database
        result = await db.execute(
            select(User).where(User.email == token_data.username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get user permissions
        user_permissions = get_user_role_permissions(
            user.role,
            user.permissions if user.permissions else None
        )

        # Check if user has all required permissions
        missing = self.required - user_permissions
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Insufficient permissions",
                    "missing_permissions": [p.value for p in missing],
                    "user_role": user.role,
                    "user_permissions": [p.value for p in user_permissions]
                }
            )

        return token_data


def require_permission(permission: Union[Permission, List[Permission]]):
    """Decorator to require specific permission(s) on endpoint.

    Usage:
        @router.post("/admin")
        @require_permission(Permission.MANAGE_SYSTEM)
        async def admin_endpoint(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get token_data and db from kwargs or dependencies
            token_data = kwargs.get('token_data')
            db = kwargs.get('db')

            if not token_data or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission checker requires token_data and db dependencies"
                )

            # Get user
            result = await db.execute(
                select(User).where(User.email == token_data.username)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Get permissions
            user_permissions = get_user_role_permissions(
                user.role,
                user.permissions if user.permissions else None
            )

            # Check permissions
            required = permission if isinstance(permission, set) else (
                {permission} if isinstance(permission, Permission) else set(permission)
            )

            missing = required - user_permissions
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": "Insufficient permissions",
                        "missing_permissions": [p.value for p in missing],
                        "user_role": user.role
                    }
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Common permission checkers for dependency injection
require_admin = PermissionChecker([Permission.VIEW_AUDIT_LOGS, Permission.VIEW_ANALYTICS])
require_superuser = PermissionChecker([Permission.MANAGE_SYSTEM])
require_user_manage = PermissionChecker([Permission.USER_MANAGE_ROLES])
require_project_delete = PermissionChecker([Permission.PROJECT_DELETE])


# Helper functions for checking user roles
async def get_user_from_token(
    token_data: TokenData = Depends(JWTBearer()),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, AsyncSession]:
    """Get user and db session from token."""
    result = await db.execute(
        select(User).where(User.email == token_data.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user, db


async def require_role(role: Union[Role, str]):
    """Check if user has at least the specified role.

    Args:
        role: Required role or role name

    Returns:
        bool: True if user has required role or higher

    Raises:
        HTTPException: If user doesn't have required role
    """
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )

    role_hierarchy = {
        Role.USER: 1,
        Role.ADMIN: 2,
        Role.SUPERUSER: 3,
    }

    required_level = role_hierarchy.get(role, 0)

    async def role_checker(
        token_data: TokenData = Depends(JWTBearer()),
        db: AsyncSession = Depends(get_db),
    ) -> TokenData:
        result = await db.execute(
            select(User).where(User.email == token_data.username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_level = role_hierarchy.get(Role(user.role) if isinstance(user.role, str) else user.role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"Requires {role.value} role or higher",
                    "user_role": user.role
                }
            )

        return token_data

    return role_checker
