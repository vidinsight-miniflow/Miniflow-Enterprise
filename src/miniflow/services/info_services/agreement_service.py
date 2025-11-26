from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.utils.pagination_params import PaginationParams
from src.miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)
from src.miniflow.utils.helpers.encryption_helper import hash_data


class AgreementService:
    """Agreement versiyonlarını yönetir"""

    def __init__(self):
        self._registry = RepositoryRegistry()
        self._agreement_version_repo = self._registry.agreement_version_repository

    @with_readonly_session(manager=None)
    def get_active_agreement(
        self,
        session,
        *,
        agreement_type: str,
        locale: str = "tr-TR",
    ) -> Dict[str, Any]:
        """Get active agreement version"""
        agreement = self._agreement_version_repo._get_active(
            session, agreement_type=agreement_type, locale=locale, include_deleted=False
        )
        if not agreement:
            raise ResourceNotFoundError(
                resource_name="agreement_version",
                message=f"No active agreement found for type {agreement_type} and locale {locale}"
            )
        
        return agreement.to_dict()

    @with_transaction(manager=None)
    def seed_agreement(self, session, *, agreements_data: List[Dict]):
        """Seed agreements (legacy method for backward compatibility)"""
        stats = {"created": 0, "skipped": 0, "updated": 0}

        for agreement_data in agreements_data:
            agreement_type = agreement_data.get("agreement_type")
            version = agreement_data.get("version")
            locale = agreement_data.get("locale", "tr-TR")

            if not agreement_type or not version:
                continue

            existing_agreement = self._agreement_version_repo._get_by_type_and_version(
                session,
                agreement_type=agreement_type,
                version=version,
                locale=locale
            )

            if existing_agreement:
                stats["skipped"] += 1
            else:
                self._agreement_version_repo._create(session, **agreement_data)
                stats["created"] += 1

        return stats