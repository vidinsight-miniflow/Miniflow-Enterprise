"""
Authentication routes for user registration, login, logout, and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional

from qbitra.api.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    LogoutResponse,
    UserInfoResponse,
)
from qbitra.api.dependencies.auth.jwt_auth import authenticate_user, AuthenticatedUser
from qbitra.domain.services import LoginService, RegistrationService
from qbitra.api.dependencies.service_providers import get_login_service, get_registration_service
from qbitra.core.qbitra_logger import get_logger

# API katmanı auth router logger'ı (logs/api/auth_routes/service.log)
logger = get_logger("auth_routes", parent_folder="api")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Kullanıcı kaydı",
    description="Yeni kullanıcı kaydı oluşturur ve email doğrulama tokeni döner."
)
async def register(
    request: RegisterRequest,
    registration_service: RegistrationService = Depends(get_registration_service),
):
    """
    Kullanıcı kaydı endpoint'i.
    
    - **username**: Kullanıcı adı (3-50 karakter, harf/rakam/alt çizgi/tire)
    - **email**: E-posta adresi
    - **password**: Şifre (min 8 karakter, büyük/küçük harf, rakam, özel karakter)
    - **name**: Ad
    - **surname**: Soyad
    - **country_code**: ISO ülke kodu (opsiyonel)
    - **phone_number**: Telefon numarası (opsiyonel)
    
    Başarılı kayıt sonrası email doğrulama tokeni döner.
    """
    try:
        result = registration_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            name=request.name,
            surname=request.surname,
            country_code=request.country_code,
            phone_number=request.phone_number,
        )
        return RegisterResponse(**result)
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        raise


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı girişi",
    description="Kullanıcı girişi yapar ve access/refresh token döner."
)
async def login(
    request: LoginRequest,
    login_service: LoginService = Depends(get_login_service),
):
    """
    Kullanıcı girişi endpoint'i.
    
    - **email_or_username**: E-posta veya kullanıcı adı
    - **password**: Şifre
    
    Başarılı giriş sonrası access_token ve refresh_token döner.
    """
    try:
        result = login_service.login(
            email_or_username=request.email_or_username,
            password=request.password,
        )
        return LoginResponse(**result)
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        raise


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı çıkışı",
    description="Mevcut oturumu sonlandırır."
)
async def logout(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    login_service: LoginService = Depends(get_login_service),
):
    """
    Kullanıcı çıkışı endpoint'i.
    
    Authorization header'ında Bearer token bekler.
    Mevcut oturumu sonlandırır.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = authorization.replace("Bearer ", "")
    
    try:
        result = login_service.logout(access_token=access_token)
        return LogoutResponse(**result)
    except Exception as e:
        logger.error(f"Logout failed: {e}", exc_info=True)
        raise


@router.post(
    "/logout-all",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Tüm oturumları sonlandır",
    description="Kullanıcının tüm aktif oturumlarını sonlandırır."
)
async def logout_all(
    current_user: AuthenticatedUser = Depends(authenticate_user),
    login_service: LoginService = Depends(get_login_service),
):
    """
    Tüm oturumları sonlandırma endpoint'i.
    
    Kullanıcının tüm aktif oturumlarını sonlandırır.
    Authentication gerektirir.
    """
    try:
        result = login_service.logout_all(user_id=current_user["user_id"])
        return LogoutResponse(**result)
    except Exception as e:
        logger.error(f"Logout all failed: {e}", exc_info=True)
        raise


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Token yenileme",
    description="Refresh token kullanarak yeni access ve refresh token alır."
)
async def refresh_token(
    request: RefreshTokenRequest,
    login_service: LoginService = Depends(get_login_service),
):
    """
    Token yenileme endpoint'i.
    
    - **refresh_token**: Refresh token
    
    Yeni access_token ve refresh_token döner.
    """
    try:
        result = login_service.refresh_tokens(refresh_token=request.refresh_token)
        return TokenResponse(**result)
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        raise


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Email doğrulama",
    description="Email doğrulama tokeni ile email'i doğrular."
)
async def verify_email(
    request: VerifyEmailRequest,
    registration_service: RegistrationService = Depends(get_registration_service),
):
    """
    Email doğrulama endpoint'i.
    
    - **verification_token**: Email doğrulama tokeni
    
    Email'i doğrular ve kullanıcı bilgilerini döner.
    """
    try:
        result = registration_service.verify_email(verification_token=request.verification_token)
        return VerifyEmailResponse(**result)
    except Exception as e:
        logger.error(f"Email verification failed: {e}", exc_info=True)
        raise


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Doğrulama emaili yeniden gönder",
    description="Email doğrulama tokeni yeniden gönderir."
)
async def resend_verification(
    request: ResendVerificationRequest,
    registration_service: RegistrationService = Depends(get_registration_service),
):
    """
    Doğrulama emaili yeniden gönderme endpoint'i.
    
    - **email**: E-posta adresi
    
    Yeni email doğrulama tokeni oluşturur ve gönderir.
    """
    try:
        result = registration_service.resend_verification_email(email=request.email)
        return ResendVerificationResponse(**result)
    except Exception as e:
        logger.error(f"Resend verification failed: {e}", exc_info=True)
        raise


@router.get(
    "/me",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı bilgileri",
    description="Authenticated kullanıcının bilgilerini döner."
)
async def get_current_user(
    current_user: AuthenticatedUser = Depends(authenticate_user),
):
    """
    Kullanıcı bilgileri endpoint'i.
    
    Authentication gerektirir.
    Mevcut kullanıcının bilgilerini döner.
    """
    try:
        from qbitra.domain.repositories import RepositoryRegistry
        from qbitra.infrastructure.database import with_readonly_session
        
        user_repo = RepositoryRegistry().user_repository
        
        @with_readonly_session(manager=None)
        def get_user_info(session, user_id: str):
            user = user_repo.get(session, record_id=user_id, include_deleted=False)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "surname": user.surname,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
                "is_admin": user.is_admin,
                "is_suspended": user.is_suspended,
                "is_locked": user.is_locked,
            }
        
        # Decorator ile sarmalanmış fonksiyonu çağır
        user_data = get_user_info(user_id=current_user["user_id"])
        
        return UserInfoResponse(
            message="User information retrieved successfully",
            data=user_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

