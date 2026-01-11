"""
QBitra Models Package
=====================

All application models are imported here to ensure they are registered
with the SQLAlchemy metadata.

This package serves as the central import point for all domain models.
When this package is imported, all models are automatically loaded and
registered with the database metadata.
"""

# Metadata'yı database'den import et
# Modeller bu metadata'yı kullanır ve import edildiklerinde otomatik olarak kaydedilirler
from qbitra.database.models import metadata

# User modellerini import et
# Bu import modellerin sınıf tanımlarını çalıştırır ve metadata'ya kaydeder
from .user_models import User, AuthSession, LoginHistory



__all__ = [
    "User",
    "AuthSession",
    "LoginHistory",
]
