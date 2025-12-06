from typing import Optional, Dict, Any, List, Union, BinaryIO, TextIO

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.utils.helpers.file_helper import (
    upload_file,
    delete_file as delete_file_from_storage,
    file_exists,
    read_file,
    get_workspace_file_path,
    get_folder_size,
)


class FileService:
    """
    Dosya yönetim servisi.
    
    Workspace dosyalarının yüklenmesi, okunması ve yönetimini sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    NOT: Dosya içeriği DEĞİŞTİRİLEMEZ! Yeni dosya yükleyin.
    """
    _registry = RepositoryRegistry()
    _file_repo = _registry.file_repository()
    _workspace_repo = _registry.workspace_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def upload_file(
        cls,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        uploaded_file: Union[BinaryIO, TextIO],
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Dosya yükler.
        
        Args:
            workspace_id: Workspace ID'si
            owner_id: Sahip kullanıcı ID'si
            uploaded_file: Yüklenen dosya (BinaryIO veya TextIO)
            name: Dosya adı (opsiyonel, otomatik oluşturulur)
            description: Açıklama (opsiyonel)
            tags: Etiketler (opsiyonel)
            file_metadata: Ek metadata (opsiyonel)
            
        Returns:
            {"id": str}
            
        Raises:
            BusinessRuleViolationError: Storage limiti aşıldı
            InvalidInputError: Geçersiz dosya
        """
        # Workspace kontrolü
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Workspace limitleri
        max_file_size_mb = workspace.max_file_size_mb_per_workspace
        storage_limit_mb = workspace.storage_limit_mb
        
        # Mevcut depolama kullanımı
        try:
            workspace_file_path = get_workspace_file_path(workspace_id)
            current_folder_size_bytes = get_folder_size(workspace_file_path)
            current_folder_size_mb = current_folder_size_bytes / (1024 * 1024)
        except ResourceNotFoundError:
            current_folder_size_mb = 0.0
        
        # Dosya yükle
        try:
            upload_result = upload_file(
                uploaded_file=uploaded_file,
                workspace_id=workspace_id,
                max_file_size_mb=max_file_size_mb,
            )
        except InvalidInputError:
            raise
        except Exception as e:
            raise InvalidInputError(
                field_name="file",
                message=f"File upload failed: {str(e)}"
            )
        
        file_size_bytes = upload_result["file_size"]
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Storage limiti kontrolü
        new_storage_mb = current_folder_size_mb + file_size_mb
        if new_storage_mb > storage_limit_mb:
            # Yüklenen dosyayı temizle
            try:
                delete_file_from_storage(upload_result["file_path"])
            except Exception:
                pass
            raise BusinessRuleViolationError(
                rule_name="storage_limit_exceeded",
                rule_detail=f"Current storage: {current_folder_size_mb:.2f} MB, Limit: {storage_limit_mb} MB",
                message=f"Storage limit exceeded. Current: {current_folder_size_mb:.2f} MB, Limit: {storage_limit_mb} MB"
            )
        
        # Dosya adı
        file_name = name if name else upload_result["file_name"]
        original_filename = getattr(uploaded_file, 'filename', upload_result["file_name"])
        
        # Benzersizlik kontrolü
        existing = cls._file_repo._get_by_name(
            session, 
            workspace_id=workspace_id, 
            name=file_name
        )
        if existing:
            # Yüklenen dosyayı temizle
            try:
                delete_file_from_storage(upload_result["file_path"])
            except Exception:
                pass
            raise ResourceAlreadyExistsError(
                resource_name="File",
                conflicting_field="name",
                message=f"File with name '{file_name}' already exists in workspace {workspace_id}"
            )
        
        # Veritabanına kaydet
        file_record = cls._file_repo._create(
            session,
            workspace_id=workspace_id,
            owner_id=owner_id,
            name=file_name,
            original_filename=original_filename,
            file_path=upload_result["file_path"],
            file_size=file_size_bytes,
            mime_type=upload_result["mime_type"],
            file_extension=upload_result["extension"],
            description=description,
            tags=tags or [],
            file_metadata=file_metadata or {},
            created_by=owner_id
        )
        
        # Workspace storage güncelle
        cls._workspace_repo._update(
            session,
            record_id=workspace_id,
            current_storage_mb=new_storage_mb
        )
        
        return {"id": file_record.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_file(
        cls,
        session,
        *,
        file_id: str,
    ) -> Dict[str, Any]:
        """
        Dosya detaylarını getirir.
        
        Args:
            file_id: Dosya ID'si
            
        Returns:
            Dosya detayları
        """
        file_record = cls._file_repo._get_by_id(session, record_id=file_id)
        
        if not file_record:
            raise ResourceNotFoundError(
                resource_name="File",
                resource_id=file_id
            )
        
        return {
            "id": file_record.id,
            "workspace_id": file_record.workspace_id,
            "owner_id": file_record.owner_id,
            "name": file_record.name,
            "original_filename": file_record.original_filename,
            "file_size": file_record.file_size,
            "file_size_mb": round(file_record.file_size / (1024 * 1024), 2),
            "mime_type": file_record.mime_type,
            "file_extension": file_record.file_extension,
            "description": file_record.description,
            "tags": file_record.tags,
            "file_metadata": file_record.file_metadata,
            "created_at": file_record.created_at.isoformat() if file_record.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_files(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace'in tüm dosyalarını listeler.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {"workspace_id": str, "files": List[Dict], "count": int, "total_size_mb": float}
        """
        files = cls._file_repo._get_all_by_workspace_id(session, workspace_id=workspace_id)
        total_size = cls._file_repo._get_total_size_by_workspace_id(session, workspace_id=workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "files": [
                {
                    "id": f.id,
                    "name": f.name,
                    "original_filename": f.original_filename,
                    "file_size": f.file_size,
                    "file_size_mb": round(f.file_size / (1024 * 1024), 2),
                    "mime_type": f.mime_type,
                    "file_extension": f.file_extension,
                    "description": f.description,
                    "tags": f.tags,
                    "created_at": f.created_at.isoformat() if f.created_at else None
                }
                for f in files
            ],
            "count": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_file_content(
        cls,
        session,
        *,
        file_id: str,
    ) -> bytes:
        """
        Dosya içeriğini okur.
        
        Args:
            file_id: Dosya ID'si
            
        Returns:
            Dosya içeriği (bytes)
        """
        file_record = cls._file_repo._get_by_id(session, record_id=file_id)
        
        if not file_record:
            raise ResourceNotFoundError(
                resource_name="File",
                resource_id=file_id
            )
        
        if not file_exists(file_record.file_path):
            raise ResourceNotFoundError(
                resource_name="File",
                resource_id=file_id
            )
        
        return read_file(file_record.file_path)

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_file(
        cls,
        session,
        *,
        file_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Dosya meta bilgilerini günceller.
        
        NOT: Dosya içeriği DEĞİŞTİRİLEMEZ! Yeni dosya yükleyin.
        
        Args:
            file_id: Dosya ID'si
            name: Yeni ad (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            tags: Yeni etiketler (opsiyonel)
            
        Returns:
            Güncellenmiş dosya bilgileri
        """
        file_record = cls._file_repo._get_by_id(session, record_id=file_id)
        
        if not file_record:
            raise ResourceNotFoundError(
                resource_name="File",
                resource_id=file_id
            )
        
        update_data = {}
        
        # Name değişikliği
        if name is not None and name != file_record.name:
            if not name.strip():
                raise InvalidInputError(
                    field_name="name",
                    message="File name cannot be empty"
                )
            # Benzersizlik kontrolü
            existing = cls._file_repo._get_by_name(
                session, 
                workspace_id=file_record.workspace_id, 
                name=name
            )
            if existing and existing.id != file_id:
                raise ResourceAlreadyExistsError(
                    resource_name="File",
                    conflicting_field="name",
                    message=f"File with name '{name}' already exists in workspace {workspace_id}"
                )
            update_data["name"] = name
        
        if description is not None:
            update_data["description"] = description
        if tags is not None:
            update_data["tags"] = tags
        
        if update_data:
            cls._file_repo._update(session, record_id=file_id, **update_data)
        
        return cls.get_file(session, file_id=file_id)

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_file(
        cls,
        session,
        *,
        file_id: str,
    ) -> Dict[str, Any]:
        """
        Dosyayı siler (hem storage hem veritabanı).
        
        Args:
            file_id: Dosya ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        file_record = cls._file_repo._get_by_id(session, record_id=file_id)
        
        if not file_record:
            raise ResourceNotFoundError(
                resource_name="File",
                resource_id=file_id
            )
        
        workspace_id = file_record.workspace_id
        file_path = file_record.file_path
        file_size_mb = file_record.file_size / (1024 * 1024)
        
        # Storage'dan sil
        try:
            if file_exists(file_path):
                delete_file_from_storage(file_path)
        except Exception:
            pass
        
        # Veritabanından sil
        cls._file_repo._delete(session, record_id=file_id)
        
        # Workspace storage güncelle
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if workspace:
            try:
                workspace_file_path = get_workspace_file_path(workspace_id)
                current_folder_size_bytes = get_folder_size(workspace_file_path)
                new_storage_mb = current_folder_size_bytes / (1024 * 1024)
            except ResourceNotFoundError:
                new_storage_mb = 0.0
            
            cls._workspace_repo._update(
                session,
                record_id=workspace_id,
                current_storage_mb=new_storage_mb
            )
        
        return {
            "success": True,
            "deleted_id": file_id
        }

