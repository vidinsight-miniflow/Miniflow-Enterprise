from functools import lru_cache
from qbitra.domain.services import *

@lru_cache(maxsize=1)
def get_registration_service() -> RegistrationService:
    return RegistrationService()

@lru_cache(maxsize=1)
def get_login_service() -> LoginService:
    return LoginService()