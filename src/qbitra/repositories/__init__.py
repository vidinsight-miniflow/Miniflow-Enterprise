from .user_repo import UserRepository, AuthSessionRepository, LoginHistoryRepository

class RepositoryRegistry:
    @property
    def user_repository(self):
        return UserRepository()
    
    @property
    def auth_session_repository(self):
        return AuthSessionRepository()
    
    @property
    def login_history_repository(self):
        return LoginHistoryRepository()


__all__ = [
    "RepositoryRegistry",
]