from typing import Optional, Dict, Any, List

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import DatabaseType
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger
from miniflow.utils.helpers.encryption_helper import encrypt_data, decrypt_data

# Logger instance
logger = get_logger(__name__)

class DatabaseService:
    """
    Database bağlantı yönetim servisi.
    
    Workspace database bağlantılarının oluşturulması ve yönetimini sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _database_repo = _registry.database_repository()
    _workspace_repo = _registry.workspace_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_database(
        cls,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        name: str,
        database_type: DatabaseType,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        connection_string: Optional[str] = None,
        ssl_enabled: bool = False,
        additional_params: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Database bağlantısı oluşturur.
        
        Args:
            workspace_id: Workspace ID'si
            owner_id: Sahip kullanıcı ID'si
            name: Bağlantı adı (workspace içinde benzersiz)
            database_type: Veritabanı tipi
            host: Sunucu adresi (opsiyonel)
            port: Port numarası (opsiyonel)
            database_name: Veritabanı adı (opsiyonel)
            username: Kullanıcı adı (opsiyonel)
            password: Şifre (opsiyonel, şifrelenir)
            connection_string: Connection string (opsiyonel, host'a alternatif)
            ssl_enabled: SSL kullanılıyor mu?
            additional_params: Ek parametreler (opsiyonel)
            description: Açıklama (opsiyonel)
            tags: Etiketler (opsiyonel)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Database name cannot be empty"
            )
        
        # Host veya connection_string zorunlu
        if not connection_string and not host:
            raise InvalidInputError(
                field_name="host",
                message="Either host or connection_string must be provided"
            )
        
        # Benzersizlik kontrolü
        existing = cls._database_repo._get_by_name(
            session, 
            workspace_id=workspace_id, 
            name=name
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Database",
                conflicting_field="name",
                message=f"Database with name '{name}' already exists in workspace {workspace_id}"
            )
        
        # Şifre şifreleme
        encrypted_password = encrypt_data(password) if password else None
        
        # Database oluştur
        database = cls._database_repo._create(
            session,
            workspace_id=workspace_id,
            owner_id=owner_id,
            name=name,
            database_type=database_type,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=encrypted_password,
            connection_string=connection_string,
            ssl_enabled=ssl_enabled,
            additional_params=additional_params or {},
            description=description,
            tags=tags or [],
            is_active=True,
            created_by=owner_id
        )
        
        return {"id": database.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_database(
        cls,
        session,
        *,
        database_id: str,
        include_password: bool = False,
    ) -> Dict[str, Any]:
        """
        Database detaylarını getirir.
        
        Args:
            database_id: Database ID'si
            include_password: Şifreyi dahil et (varsayılan: False)
            
        Returns:
            Database detayları
        """
        database = cls._database_repo._get_by_id(session, record_id=database_id, raise_not_found=True)
        
        result = {
            "id": database.id,
            "workspace_id": database.workspace_id,
            "owner_id": database.owner_id,
            "name": database.name,
            "database_type": database.database_type.value if database.database_type else None,
            "host": database.host,
            "port": database.port,
            "database_name": database.database_name,
            "username": database.username,
            "ssl_enabled": database.ssl_enabled,
            "additional_params": database.additional_params,
            "description": database.description,
            "tags": database.tags,
            "is_active": database.is_active,
            "last_tested_at": database.last_tested_at.isoformat() if database.last_tested_at else None,
            "last_test_status": database.last_test_status,
            "created_at": database.created_at.isoformat() if database.created_at else None
        }
        
        # Şifre
        if include_password and database.password:
            result["password"] = decrypt_data(database.password)
        else:
            result["password"] = "********" if database.password else None
        
        # Connection string (varsa)
        result["connection_string"] = database.connection_string
        
        return result

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_databases(
        cls,
        session,
        *,
        workspace_id: str,
        database_type: Optional[DatabaseType] = None,
    ) -> Dict[str, Any]:
        """
        Workspace'in tüm database bağlantılarını listeler.
        
        Args:
            workspace_id: Workspace ID'si
            database_type: Filtre için database tipi (opsiyonel)
            
        Returns:
            {"workspace_id": str, "databases": List[Dict], "count": int}
        """
        if database_type:
            databases = cls._database_repo._get_by_type(
                session, 
                workspace_id=workspace_id, 
                database_type=database_type
            )
        else:
            databases = cls._database_repo._get_all_by_workspace_id(
                session, 
                workspace_id=workspace_id
            )
        
        return {
            "workspace_id": workspace_id,
            "databases": [
                {
                    "id": db.id,
                    "name": db.name,
                    "database_type": db.database_type.value if db.database_type else None,
                    "host": db.host,
                    "port": db.port,
                    "database_name": db.database_name,
                    "description": db.description,
                    "tags": db.tags,
                    "is_active": db.is_active,
                    "last_tested_at": db.last_tested_at.isoformat() if db.last_tested_at else None,
                    "last_test_status": db.last_test_status
                }
                for db in databases
            ],
            "count": len(databases)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_database(
        cls,
        session,
        *,
        database_id: str,
        name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        connection_string: Optional[str] = None,
        ssl_enabled: Optional[bool] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Database bağlantı bilgilerini günceller.
        
        Args:
            database_id: Database ID'si
            (diğer parametreler opsiyonel)
            
        Returns:
            Güncellenmiş database bilgileri
        """
        database = cls._database_repo._get_by_id(session, record_id=database_id)
        
        if not database:
            raise ResourceNotFoundError(
                resource_name="Database",
                resource_id=database_id
            )
        
        update_data = {}
        
        # Name değişikliği
        if name is not None and name != database.name:
            if not name.strip():
                raise InvalidInputError(
                    field_name="name",
                    message="Database name cannot be empty"
                )
            # Benzersizlik kontrolü
            existing = cls._database_repo._get_by_name(
                session, 
                workspace_id=database.workspace_id, 
                name=name
            )
            if existing and existing.id != database_id:
                raise ResourceAlreadyExistsError(
                    resource_name="Database",
                    conflicting_field="name",
                    message=f"Database with name '{name}' already exists in workspace {database.workspace_id}"
                )
            update_data["name"] = name
        
        if host is not None:
            update_data["host"] = host
        if port is not None:
            update_data["port"] = port
        if database_name is not None:
            update_data["database_name"] = database_name
        if username is not None:
            update_data["username"] = username
        if password is not None:
            update_data["password"] = encrypt_data(password)
        if connection_string is not None:
            update_data["connection_string"] = connection_string
        if ssl_enabled is not None:
            update_data["ssl_enabled"] = ssl_enabled
        if additional_params is not None:
            update_data["additional_params"] = additional_params
        if description is not None:
            update_data["description"] = description
        if tags is not None:
            update_data["tags"] = tags
        
        if update_data:
            cls._database_repo._update(session, record_id=database_id, **update_data)
        
        return cls.get_database(database_id=database_id)

    # ==================================================================================== TEST CONNECTION ==
    @classmethod
    @with_transaction(manager=None)
    def update_test_status(
        cls,
        session,
        *,
        database_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """
        Database bağlantı test durumunu günceller.
        
        Args:
            database_id: Database ID'si
            status: Test durumu (SUCCESS, FAILED)
            
        Returns:
            {"success": True, "status": str}
        """
        database = cls._database_repo._get_by_id(session, record_id=database_id)
        
        if not database:
            raise ResourceNotFoundError(
                resource_name="Database",
                resource_id=database_id
            )
        
        cls._database_repo._update_test_status(
            session, 
            database_id=database_id, 
            status=status
        )
        
        return {
            "success": True,
            "status": status
        }

    # ==================================================================================== ACTIVATE/DEACTIVATE ==
    @classmethod
    @with_transaction(manager=None)
    def deactivate_database(
        cls,
        session,
        *,
        database_id: str,
    ) -> Dict[str, Any]:
        """
        Database bağlantısını deaktive eder.
        
        Args:
            database_id: Database ID'si
            
        Returns:
            {"success": True}
        """
        database = cls._database_repo._get_by_id(session, record_id=database_id)
        
        if not database:
            raise ResourceNotFoundError(
                resource_name="Database",
                resource_id=database_id
            )
        
        cls._database_repo._deactivate(session, database_id=database_id)
        
        return {"success": True, "is_active": False}

    @classmethod
    @with_transaction(manager=None)
    def activate_database(
        cls,
        session,
        *,
        database_id: str,
    ) -> Dict[str, Any]:
        """
        Database bağlantısını aktive eder.
        
        Args:
            database_id: Database ID'si
            
        Returns:
            {"success": True}
        """
        database = cls._database_repo._get_by_id(session, record_id=database_id)
        
        if not database:
            raise ResourceNotFoundError(
                resource_name="Database",
                resource_id=database_id
            )
        
        cls._database_repo._activate(session, database_id=database_id)
        
        return {"success": True, "is_active": True}

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_database(
        cls,
        session,
        *,
        database_id: str,
    ) -> Dict[str, Any]:
        """
        Database bağlantısını siler.
        
        Args:
            database_id: Database ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        database = cls._database_repo._get_by_id(session, record_id=database_id)
        
        if not database:
            raise ResourceNotFoundError(
                resource_name="Database",
                resource_id=database_id
            )
        
        cls._database_repo._delete(session, record_id=database_id)
        
        return {
            "success": True,
            "deleted_id": database_id
        }

