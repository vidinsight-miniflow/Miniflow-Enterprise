from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.utils.pagination_params import PaginationParams
from src.miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)



class ExecutionInputService:
    def __init__(self):
        self._registry = RepositoryRegistry()
        self._execution_input_repo = self._registry.execution_input_repository