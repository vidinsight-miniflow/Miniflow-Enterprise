from typing import Optional, Dict, Any, List

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger
from miniflow.utils.helpers.file_helper import (
    upload_global_script,
    delete_file,
)


class GlobalScriptService:
    """
    Global (Sistem) script yönetim servisi.
    
    Sistemde tanımlı hazır script'lerin yönetimini sağlar.
    Bu script'ler tüm workspace'lerde kullanılabilir.
    NOT: Script içeriği oluşturulduktan sonra DEĞİŞTİRİLEMEZ (güvenlik).
    """
    _registry = RepositoryRegistry()
    _script_repo = _registry.script_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_script(
        cls,
        session,
        *,
        name: str,
        category: str,
        content: str,
        description: Optional[str] = None,
        subcategory: Optional[str] = None,
        script_metadata: Optional[Dict[str, Any]] = None,
        required_packages: Optional[List[str]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Global script oluşturur.
        
        Args:
            name: Script adı (global olarak benzersiz)
            category: Kategori (zorunlu)
            content: Script içeriği
            description: Açıklama (opsiyonel)
            subcategory: Alt kategori (opsiyonel)
            script_metadata: Meta veriler (opsiyonel)
            required_packages: Gerekli paketler (opsiyonel)
            input_schema: Input şeması (opsiyonel)
            output_schema: Output şeması (opsiyonel)
            tags: Etiketler (opsiyonel)
            documentation_url: Dökümantasyon URL'i (opsiyonel)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Script name cannot be empty"
            )
        
        if not category or not category.strip():
            raise InvalidInputError(
                field_name="category",
                message="Script category cannot be empty"
            )
        
        if not content or not content.strip():
            raise InvalidInputError(
                field_name="content",
                message="Script content cannot be empty"
            )
        
        # Benzersizlik kontrolü
        existing = cls._script_repo._get_by_name(session, name=name)
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Script",
                conflicting_field="name",
                message=f"Global script with name '{name}' already exists"
            )
        
        # Script dosyasını yükle
        file_extension = ".py"
        try:
            upload_result = upload_global_script(
                content=content,
                script_name=name,
                extension=file_extension,
                category=category,
                subcategory=subcategory
            )
            file_path = upload_result["file_path"]
            file_size = upload_result["file_size"]
        except Exception as e:
            raise InvalidInputError(
                field_name="content",
                message=f"Failed to upload script: {str(e)}"
            )
        
        # Script oluştur
        script = cls._script_repo._create(
            session,
            name=name,
            category=category,
            description=description,
            subcategory=subcategory,
            file_extension=file_extension,
            file_path=file_path,
            file_size=file_size,
            content=content,
            script_metadata=script_metadata or {},
            required_packages=required_packages or [],
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            tags=tags or [],
            documentation_url=documentation_url,
            created_by="system"
        )
        
        return {"id": script.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_script(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script detaylarını getirir (content hariç).
        
        Args:
            script_id: Script ID'si
            
        Returns:
            Script detayları
        """
        script = cls._script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="Script",
                resource_id=script_id
            )
        
        return {
            "id": script.id,
            "name": script.name,
            "description": script.description,
            "category": script.category,
            "subcategory": script.subcategory,
            "file_extension": script.file_extension,
            "file_size": script.file_size,
            "script_metadata": script.script_metadata,
            "required_packages": script.required_packages,
            "input_schema": script.input_schema,
            "output_schema": script.output_schema,
            "tags": script.tags,
            "documentation_url": script.documentation_url,
            "created_at": script.created_at.isoformat() if script.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_script_by_name(
        cls,
        session,
        *,
        name: str,
    ) -> Dict[str, Any]:
        """
        Script'i isimle getirir.
        
        Args:
            name: Script adı
            
        Returns:
            Script detayları
        """
        script = cls._script_repo._get_by_name(session, name=name)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="Script",
                resource_id=name
            )
        
        return {
            "id": script.id,
            "name": script.name,
            "description": script.description,
            "category": script.category,
            "subcategory": script.subcategory,
            "file_extension": script.file_extension,
            "file_size": script.file_size,
            "required_packages": script.required_packages,
            "tags": script.tags
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_script_content(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script içeriğini ve şemalarını getirir.
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"content": str, "input_schema": Dict, "output_schema": Dict}
        """
        script = cls._script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="Script",
                resource_id=script_id
            )
        
        return {
            "content": script.content,
            "input_schema": script.input_schema,
            "output_schema": script.output_schema
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_all_scripts(
        cls,
        session,
        *,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tüm script'leri listeler.
        
        Args:
            category: Kategori filtresi (opsiyonel)
            subcategory: Alt kategori filtresi (opsiyonel)
            
        Returns:
            {"scripts": List[Dict], "count": int}
        """
        if category and subcategory:
            scripts = cls._script_repo._get_by_category_and_subcategory(
                session, 
                category=category, 
                subcategory=subcategory
            )
        elif category:
            scripts = cls._script_repo._get_by_category(session, category=category)
        else:
            scripts = cls._script_repo._get_all(session)
        
        return {
            "scripts": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "category": s.category,
                    "subcategory": s.subcategory,
                    "file_size": s.file_size,
                    "required_packages": s.required_packages,
                    "tags": s.tags,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in scripts
            ],
            "count": len(scripts)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_categories(
        cls,
        session,
    ) -> Dict[str, Any]:
        """
        Mevcut kategorileri listeler.
        
        Returns:
            {"categories": List[str]}
        """
        categories = cls._script_repo._get_categories(session)
        
        return {"categories": categories}

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_script(
        cls,
        session,
        *,
        script_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Script meta bilgilerini günceller.
        
        NOT: Script içeriği DEĞİŞTİRİLEMEZ! Güvenlik nedeniyle yeni script oluşturun.
        
        Args:
            script_id: Script ID'si
            description: Yeni açıklama (opsiyonel)
            tags: Yeni etiketler (opsiyonel)
            documentation_url: Yeni dökümantasyon URL'i (opsiyonel)
            
        Returns:
            Güncellenmiş script bilgileri
        """
        script = cls._script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="Script",
                resource_id=script_id
            )
        
        update_data = {}
        if description is not None:
            update_data["description"] = description
        if tags is not None:
            update_data["tags"] = tags
        if documentation_url is not None:
            update_data["documentation_url"] = documentation_url
        
        if update_data:
            update_data["updated_by"] = "system"
            cls._script_repo._update(session, record_id=script_id, **update_data)
        
        return cls.get_script(script_id=script_id)

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_script(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script'i siler (dosya + veritabanı).
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        script = cls._script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="Script",
                resource_id=script_id
            )
        
        # Dosyayı sil
        if script.file_path:
            try:
                delete_file(script.file_path)
            except Exception:
                pass
        
        # Veritabanından sil
        cls._script_repo._delete(session, record_id=script_id)
        
        return {
            "success": True,
            "deleted_id": script_id
        }

    # ==================================================================================== SEED ==
    @classmethod
    @with_transaction(manager=None)
    def seed_scripts(
        cls,
        session,
        *,
        scripts_data: List[Dict],
    ) -> Dict[str, Any]:
        """
        Global script'leri seed eder (başlangıç verisi).
        
        Args:
            scripts_data: Script verileri listesi
            
        Returns:
            {"created": int, "skipped": int}
        """
        stats = {"created": 0, "skipped": 0}
        
        for script_data in scripts_data:
            script_name = script_data.get("name")
            if not script_name:
                stats["skipped"] += 1
                continue
            
            # Zaten var mı?
            existing = cls._script_repo._get_by_name(session, name=script_name)
            if existing:
                stats["skipped"] += 1
                continue
            
            try:
                category = script_data.get("category")
                content = script_data.get("content")
                
                if not category or not content:
                    stats["skipped"] += 1
                    continue
                
                # Script dosyasını yükle
                file_extension = ".py"
                subcategory = script_data.get("subcategory")
                
                upload_result = upload_global_script(
                    content=content,
                    script_name=script_name,
                    extension=file_extension,
                    category=category,
                    subcategory=subcategory
                )
                
                # Script oluştur
                cls._script_repo._create(
                    session,
                    name=script_name,
                    category=category,
                    description=script_data.get("description"),
                    subcategory=subcategory,
                    file_extension=file_extension,
                    file_path=upload_result["file_path"],
                    file_size=upload_result["file_size"],
                    content=content,
                    script_metadata=script_data.get("script_metadata", {}),
                    required_packages=script_data.get("required_packages", []),
                    input_schema=script_data.get("input_schema", {}),
                    output_schema=script_data.get("output_schema", {}),
                    tags=script_data.get("tags", []),
                    documentation_url=script_data.get("documentation_url"),
                    created_by="system"
                )
                stats["created"] += 1
            except Exception:
                stats["skipped"] += 1
        
        return stats

