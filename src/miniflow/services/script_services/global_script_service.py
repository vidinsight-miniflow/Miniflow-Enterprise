from typing import Optional, Dict, Any, List

from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.utils.pagination_params import PaginationParams
from src.miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)
from src.miniflow.utils.helpers.file_helper import (
    upload_global_script,
    delete_file,
)


class GlobalScriptService:
    def __init__(self):
        self._registry = RepositoryRegistry()
        self._script_repo = self._registry.script_repository

    def _get_script_dict(self, script) -> Dict[str, Any]:
        """Helper method to convert script to dict"""
        return {
            "id": script.id,
            "name": script.name,
            "description": script.description,
            "file_extension": script.file_extension,
            "file_size": script.file_size,
            "file_path": script.file_path,
            "category": script.category,
            "subcategory": script.subcategory,
            "required_packages": script.required_packages,
            "tags": script.tags,
            "documentation_url": script.documentation_url,
        }

    @with_transaction(manager=None)
    def create_script(
        self,
        session,
        *,
        name: str,
        category: str,
        description: Optional[str] = None,
        subcategory: Optional[str] = None,
        content: str = None,
        script_metadata: Optional[Dict[str, Any]] = None,
        required_packages: Optional[List[str]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new global script"""
        # Validate inputs
        if not name or not name.strip():
            raise InvalidInputError(field_name="name", message="Script name cannot be empty")
        
        if not category or not category.strip():
            raise InvalidInputError(field_name="category", message="Script category cannot be empty")
        
        if content is None or not content.strip():
            raise InvalidInputError(field_name="content", message="Script content cannot be empty")
        
        # Check if script name already exists globally
        existing = self._script_repo._get_by_name(session, name=name, include_deleted=False)
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="script",
                conflicting_field="name",
                message=f"Script with name '{name}' already exists"
            )

        # Check if script exists in this category and subcategory
        existing_in_category = self._script_repo._get_by_name_and_category_and_subcategory(
            session,
            name=name,
            category=category,
            subcategory=subcategory,
            include_deleted=False
        )
        if existing_in_category:
            raise ResourceAlreadyExistsError(
                resource_name="script",
                conflicting_field="name",
                message=f"Script with name '{name}' already exists in category '{category}' and subcategory '{subcategory or 'None'}'"
            )
        
        # Upload script file using file helper (handles all file operations, validation, etc.)
        file_extension = ".py"
        upload_result = upload_global_script(
            content=content,
            script_name=name,
            extension=file_extension,
            category=category,
            subcategory=subcategory
        )
        file_path = upload_result["file_path"]
        file_size = upload_result["file_size"]
        
        # Create script
        script = self._script_repo._create(
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
            created_by="system",
        )
        
        return self._get_script_dict(script)

    @with_readonly_session(manager=None)
    def get_script(
        self,
        session,
        *,
        script_id: str
    ) -> Dict[str, Any]:
        """Get script by ID"""
        script = self._script_repo._get_by_id(session, record_id=script_id, include_deleted=False)
        if not script:
            raise ResourceNotFoundError(resource_name="script", resource_id=script_id)
        
        return self._get_script_dict(script)

    @with_readonly_session(manager=None)
    def get_script_content(
        self,
        session,
        *,
        script_id: str
    ) -> Dict[str, Any]:
        """Get script content, input schema and output schema"""
        script = self._script_repo._get_by_id(session, record_id=script_id, include_deleted=False)
        if not script:
            raise ResourceNotFoundError(resource_name="script", resource_id=script_id)
        
        return {
            "content": script.content,
            "input_schema": script.input_schema,
            "output_schema": script.output_schema,
        }
    
    @with_transaction(manager=None)
    def update_script(
        self,
        session,
        *,
        script_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update script metadata"""
        script = self._script_repo._get_by_id(session, record_id=script_id, include_deleted=False)
        if not script:
            raise ResourceNotFoundError(resource_name="script", resource_id=script_id)
        
        update_data = {}
        if description is not None:
            update_data["description"] = description
        if tags is not None:
            update_data["tags"] = tags
        if documentation_url is not None:
            update_data["documentation_url"] = documentation_url
        
        update_data["updated_by"] = "system"
        
        updated_script = self._script_repo._update(session, record_id=script_id, **update_data)
        
        return self._get_script_dict(updated_script)

    @with_transaction(manager=None)
    def delete_script(
        self,
        session,
        *,
        script_id: str
    ) -> Dict[str, Any]:
        """Delete script and its file"""
        script = self._script_repo._get_by_id(session, record_id=script_id, include_deleted=False)
        if not script:
            raise ResourceNotFoundError(resource_name="script", resource_id=script_id)
        
        # Delete file if it exists
        if script.file_path:
            try:
                delete_file(script.file_path)
            except Exception as e:
                # Log error but continue with deletion
                # File might already be deleted or not exist
                pass
        
        self._script_repo._delete(session, record_id=script_id)
        
        return {
            "deleted": True,
            "script_id": script_id
        }

    @with_readonly_session(manager=None)
    def get_all_scripts(
        self,
        session,
        *,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False,
        category: Optional[str] = None,
        subcategory: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all scripts with pagination and filters"""
        pagination_params = PaginationParams(
            page=page,
            page_size=page_size,
            order_by=order_by or "created_at",
            order_desc=order_desc,
            include_deleted=include_deleted
        )
        pagination_params.validate()
        
        filter_kwargs = {}
        if category:
            filter_kwargs['category'] = category
        if subcategory:
            filter_kwargs['subcategory'] = subcategory
        
        result = self._script_repo._paginate(
            session,
            pagination_params=pagination_params,
            **filter_kwargs
        )
        
        items = [self._get_script_dict(script) for script in result.items]
        
        return {
            "items": items,
            "metadata": result.metadata.to_dict()
        }