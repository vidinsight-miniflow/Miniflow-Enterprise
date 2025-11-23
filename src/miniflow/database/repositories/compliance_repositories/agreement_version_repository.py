from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ..base_repository import BaseRepository
from ...models.compliance_models.agreement_version_model import AgreementVersion


class AgreementVersionRepository(BaseRepository[AgreementVersion]):
    def __init__(self):
        super().__init__(AgreementVersion)