"""
Authentication schemas for request/response validation.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, model_serializer
import re

from qbitra.utils.handlers.configuration_handler import ConfigurationHandler


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request schema."""
    username: str = Field(..., min_length=3, max_length=50, description="Kullanıcı adı")
    email: EmailStr = Field(..., description="E-posta adresi")
    password: str = Field(..., min_length=8, description="Şifre")
    name: str = Field(..., min_length=1, max_length=100, description="Ad")
    surname: str = Field(..., min_length=1, max_length=100, description="Soyad")
    country_code: Optional[str] = Field(None, max_length=2, description="ISO ülke kodu")
    phone_number: Optional[str] = Field(None, max_length=20, description="Telefon numarası (E.164 formatı)")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', v):
            raise ValueError("Kullanıcı adı sadece harf, rakam, alt çizgi ve tire içerebilir")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Şifre en az bir büyük harf içermelidir")
        if not re.search(r'[a-z]', v):
            raise ValueError("Şifre en az bir küçük harf içermelidir")
        if not re.search(r'\d', v):
            raise ValueError("Şifre en az bir rakam içermelidir")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', v):
            raise ValueError("Şifre en az bir özel karakter içermelidir")
        return v


class LoginRequest(BaseModel):
    """User login request schema."""
    email_or_username: str = Field(..., description="E-posta veya kullanıcı adı")
    password: str = Field(..., description="Şifre")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str = Field(..., description="Refresh token")


class VerifyEmailRequest(BaseModel):
    """Email verification request schema."""
    verification_token: str = Field(..., description="Email doğrulama tokeni")


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema."""
    email: EmailStr = Field(..., description="E-posta adresi")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

def _is_development() -> bool:
    """Check if current environment is development."""
    try:
        env = ConfigurationHandler.get_current_env()
        return env in ("dev", "local", "development")
    except Exception:
        # Fallback to False (production-safe) if config not initialized
        return False


class UserData(BaseModel):
    """User data in response with environment-based transparency."""
    id: str
    username: str
    email: str
    email_verified: Optional[bool] = None
    email_verification_token: Optional[str] = None

    class Config:
        from_attributes = True

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Serialize model with environment-based field filtering."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "email_verified": self.email_verified,
        }
        
        # Only include sensitive fields in development
        if _is_development() and self.email_verification_token:
            data["email_verification_token"] = self.email_verification_token
        
        return data


class LoginResponse(BaseModel):
    """Login response schema."""
    message: str
    data: dict


class RegisterResponse(BaseModel):
    """Registration response schema with environment-based transparency."""
    message: str
    data: dict  # Using dict to allow email_verification_token in response
    
    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Serialize response with environment-based field filtering."""
        result = {
            "message": self.message,
            "data": dict(self.data)
        }
        
        # Remove sensitive fields in production
        if not _is_development():
            result["data"].pop("email_verification_token", None)
        
        return result


class TokenResponse(BaseModel):
    """Token response schema."""
    message: str
    data: dict


class VerifyEmailResponse(BaseModel):
    """Email verification response schema."""
    message: str
    data: UserData


class ResendVerificationResponse(BaseModel):
    """Resend verification response schema with environment-based transparency."""
    message: str
    data: dict
    
    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Serialize response with environment-based field filtering."""
        result = {
            "message": self.message,
            "data": dict(self.data)
        }
        
        # Remove sensitive fields in production
        if not _is_development():
            result["data"].pop("email_verification_token", None)
        
        return result


class LogoutResponse(BaseModel):
    """Logout response schema."""
    message: str
    data: dict


class UserInfoResponse(BaseModel):
    """User info response schema."""
    message: str
    data: dict

