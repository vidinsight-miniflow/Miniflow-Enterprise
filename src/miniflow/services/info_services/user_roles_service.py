from typing import Optional, Dict, List, Any

from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.utils.pagination_params import PaginationParams
from src.miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)


class UserRolesService:

    def __init__(self):
        self._registry = RepositoryRegistry()
        self._user_roles_repository = self._registry.user_roles_repository
        self._workspace_member_repo = self._registry.workspace_member_repository

    @with_transaction(manager=None)
    def seed_role(self, session, *, roles_data: List[Dict]):
        """Seed roles (legacy method for backward compatibility)"""
        stats = {"created": 0, "skipped": 0, "updated": 0}

        for role_data in roles_data:
            role_name = role_data.get("name")
            if not role_name:
                continue

            existing_role = self._user_roles_repository._get_by_name(session, name=role_name)

            if existing_role:
                stats["skipped"] += 1
            else:
                self._user_roles_repository._create(session, **role_data)
                stats["created"] += 1

        return stats