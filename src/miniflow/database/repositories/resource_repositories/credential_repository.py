from typing import List, Union
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.resource_models.credential_model import Credential
from ...models.enums import CredentialType


class CredentialRepository(BaseRepository[Credential]):
    def __init__(self):
        super().__init__(Credential)

    