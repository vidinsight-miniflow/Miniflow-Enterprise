from qbitra.infrastructure.database.repos.base import BaseRepository
from qbitra.domain.models.user_models.login_histor import LoginHistory


class LoginHistoryRepository(BaseRepository[LoginHistory]):
    
    def __init__(self):
        super().__init__(LoginHistory)