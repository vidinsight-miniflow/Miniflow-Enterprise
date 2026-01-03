from typing import Optional, Dict, Any, List

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import TriggerType
from miniflow.core.exceptions import (ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger
from miniflow.utils.handlers.configuration_handler import ConfigurationHandler


class TriggerService:
    """
    Workflow Trigger yönetim servisi.
    
    Workflow tetikleyicilerinin CRUD işlemlerini sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _trigger_repo = _registry.trigger_repository()
    _workflow_repo = _registry.workflow_repository()
    _workspace_repo = _registry.workspace_repository()
    
    # Config'den limit değerlerini al
    _config = ConfigurationHandler()
    _min_triggers_per_workflow = _config.get_int("WORKFLOW", "min_triggers_per_workflow", fallback=1)
    _max_triggers_per_workflow = _config.get_int("WORKFLOW", "max_triggers_per_workflow", fallback=10)

    # ==================================================================================== VALIDATION HELPERS ==
    @classmethod
    def _validate_input_mapping(cls, input_mapping: Dict[str, Any]) -> None:
        """
        Input mapping yapısını validate eder.
        
        Beklenen format: {VARIABLE_NAME: {type: str, value: Any}}
        """
        if not isinstance(input_mapping, dict):
            raise InvalidInputError(
                field_name="input_mapping",
                message="Input mapping must be a dictionary"
            )
        
        for variable_name, mapping_value in input_mapping.items():
            if not isinstance(variable_name, str) or not variable_name.strip():
                raise InvalidInputError(
                    field_name="input_mapping",
                    message=f"Variable name must be a non-empty string"
                )
            
            if not isinstance(mapping_value, dict):
                raise InvalidInputError(
                    field_name="input_mapping",
                    message=f"Mapping value for '{variable_name}' must be a dictionary with 'type' and 'value' keys"
                )
            
            if 'type' not in mapping_value:
                raise InvalidInputError(
                    field_name="input_mapping",
                    message=f"Mapping value for '{variable_name}' must contain 'type' key"
                )
            
            if not isinstance(mapping_value['type'], str) or not mapping_value['type'].strip():
                raise InvalidInputError(
                    field_name="input_mapping",
                    message=f"Type for '{variable_name}' must be a non-empty string"
                )
            
            if 'value' not in mapping_value:
                raise InvalidInputError(
                    field_name="input_mapping",
                    message=f"Mapping value for '{variable_name}' must contain 'value' key"
                )

    @classmethod
    def _validate_trigger_config(cls, trigger_type: TriggerType, config: Dict[str, Any]) -> None:
        """
        Trigger tipine göre config'i validate eder.
        """
        if not isinstance(config, dict):
            raise InvalidInputError(
                field_name="config",
                message="Config must be a dictionary"
            )
        
        if trigger_type == TriggerType.SCHEDULED:
            if 'cron_expression' not in config:
                raise InvalidInputError(
                    field_name="config",
                    message="SCHEDULED trigger requires 'cron_expression' in config"
                )
        
        # Diğer trigger tipleri için validasyon eklenebilir

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_trigger(
        cls,
        session,
        *,
        workspace_id: str,
        workflow_id: str,
        name: str,
        trigger_type: TriggerType,
        config: Dict[str, Any],
        created_by: str,
        description: Optional[str] = None,
        input_mapping: Optional[Dict[str, Any]] = None,
        is_enabled: bool = True,
    ) -> Dict[str, Any]:
        """
        Yeni trigger oluşturur.
        
        Args:
            workspace_id: Workspace ID'si
            workflow_id: Workflow ID'si
            name: Trigger adı (workspace içinde benzersiz)
            trigger_type: Trigger tipi (API, SCHEDULED, WEBHOOK, EVENT)
            config: Trigger konfigürasyonu
            created_by: Oluşturan kullanıcı ID'si
            description: Açıklama (opsiyonel)
            input_mapping: Input mapping kuralları (opsiyonel)
            is_enabled: Aktif mi (varsayılan: True)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Trigger name cannot be empty"
            )
        
        # Workspace kontrolü
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Workflow kontrolü
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        if workflow.workspace_id != workspace_id:
            raise InvalidInputError(
                field_name="workflow_id",
                message="Workflow does not belong to this workspace"
            )
        
        # Workflow trigger limit kontrolü
        current_triggers = cls._trigger_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        current_trigger_count = len(current_triggers)
        
        if current_trigger_count >= cls._max_triggers_per_workflow:
            raise BusinessRuleViolationError(
                rule_name="trigger_limit_reached",
                rule_detail=f"Workflow {workflow_id} has {current_trigger_count} triggers, maximum allowed: {cls._max_triggers_per_workflow}",
                message=f"Trigger limit reached for this workflow. Maximum: {cls._max_triggers_per_workflow}"
            )
        
        # Benzersizlik kontrolü
        existing = cls._trigger_repo._get_by_name(
            session,
            workspace_id=workspace_id,
            name=name
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Trigger",
                conflicting_field="name",
                message=f"Trigger with name '{name}' already exists in workflow {workflow_id}"
            )
        
        # Config validation
        cls._validate_trigger_config(trigger_type, config)
        
        # Input mapping validation
        if input_mapping:
            cls._validate_input_mapping(input_mapping)
        
        # Trigger oluştur
        trigger = cls._trigger_repo._create(
            session,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            name=name,
            trigger_type=trigger_type,
            config=config,
            description=description,
            input_mapping=input_mapping or {},
            is_enabled=is_enabled,
            created_by=created_by
        )
        
        return {"id": trigger.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_trigger(
        cls,
        session,
        *,
        trigger_id: str,
    ) -> Dict[str, Any]:
        """
        Trigger detaylarını getirir.
        
        Args:
            trigger_id: Trigger ID'si
            
        Returns:
            Trigger detayları
        """
        trigger = cls._trigger_repo._get_by_id(session, record_id=trigger_id)
        
        if not trigger:
            raise ResourceNotFoundError(
                resource_name="Trigger",
                resource_id=trigger_id
            )
        
        return {
            "id": trigger.id,
            "workspace_id": trigger.workspace_id,
            "workflow_id": trigger.workflow_id,
            "name": trigger.name,
            "description": trigger.description,
            "trigger_type": trigger.trigger_type.value if trigger.trigger_type else None,
            "config": trigger.config or {},
            "input_mapping": trigger.input_mapping or {},
            "is_enabled": trigger.is_enabled,
            "created_at": trigger.created_at.isoformat() if trigger.created_at else None,
            "updated_at": trigger.updated_at.isoformat() if trigger.updated_at else None,
            "created_by": trigger.created_by
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_triggers(
        cls,
        session,
        *,
        workspace_id: str,
        trigger_type: Optional[TriggerType] = None,
        is_enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Workspace'in trigger'larını listeler.
        
        Args:
            workspace_id: Workspace ID'si
            trigger_type: Trigger tipi filtresi (opsiyonel)
            is_enabled: Aktiflik filtresi (opsiyonel)
            
        Returns:
            {"workspace_id": str, "triggers": List[Dict], "count": int}
        """
        if trigger_type:
            triggers = cls._trigger_repo._get_by_type(
                session,
                workspace_id=workspace_id,
                trigger_type=trigger_type
            )
        elif is_enabled is not None:
            if is_enabled:
                triggers = cls._trigger_repo._get_enabled_triggers(session, workspace_id=workspace_id)
            else:
                all_triggers = cls._trigger_repo._get_all_by_workspace_id(session, workspace_id=workspace_id)
                triggers = [t for t in all_triggers if not t.is_enabled]
        else:
            triggers = cls._trigger_repo._get_all_by_workspace_id(session, workspace_id=workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "triggers": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "workflow_id": t.workflow_id,
                    "trigger_type": t.trigger_type.value if t.trigger_type else None,
                    "is_enabled": t.is_enabled
                }
                for t in triggers
            ],
            "count": len(triggers)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workflow_triggers(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'un trigger'larını listeler.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"workflow_id": str, "triggers": List[Dict], "count": int}
        """
        triggers = cls._trigger_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "triggers": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "trigger_type": t.trigger_type.value if t.trigger_type else None,
                    "config": t.config or {},
                    "is_enabled": t.is_enabled
                }
                for t in triggers
            ],
            "count": len(triggers)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_trigger(
        cls,
        session,
        *,
        trigger_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        trigger_type: Optional[TriggerType] = None,
        config: Optional[Dict[str, Any]] = None,
        input_mapping: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Trigger bilgilerini günceller.
        
        Args:
            trigger_id: Trigger ID'si
            name: Yeni ad (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            trigger_type: Yeni tip (opsiyonel)
            config: Yeni konfigürasyon (opsiyonel)
            input_mapping: Yeni input mapping (opsiyonel)
            
        Returns:
            Güncellenmiş trigger bilgileri
        """
        trigger = cls._trigger_repo._get_by_id(session, record_id=trigger_id)
        
        if not trigger:
            raise ResourceNotFoundError(
                resource_name="Trigger",
                resource_id=trigger_id
            )
        
        # Validasyonlar
        if name is not None:
            if not name.strip():
                raise InvalidInputError(
                    field_name="name",
                    message="Trigger name cannot be empty"
                )
            if name != trigger.name:
                existing = cls._trigger_repo._get_by_name(
                    session,
                    workspace_id=trigger.workspace_id,
                    name=name
                )
                if existing:
                    raise ResourceAlreadyExistsError(
                        resource_name="Trigger",
                        conflicting_field="name",
                        message=f"Trigger with name '{name}' already exists in workflow {workflow_id}"
                    )
        
        # Config validation
        new_trigger_type = trigger_type if trigger_type is not None else trigger.trigger_type
        new_config = config if config is not None else trigger.config
        
        if config is not None or trigger_type is not None:
            cls._validate_trigger_config(new_trigger_type, new_config)
        
        # Input mapping validation
        if input_mapping is not None:
            cls._validate_input_mapping(input_mapping)
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if trigger_type is not None:
            update_data["trigger_type"] = trigger_type
        if config is not None:
            update_data["config"] = config
        if input_mapping is not None:
            update_data["input_mapping"] = input_mapping
        
        if update_data:
            cls._trigger_repo._update(session, record_id=trigger_id, **update_data)
        
        return cls.get_trigger(trigger_id=trigger_id)

    # ==================================================================================== ENABLE/DISABLE ==
    @classmethod
    @with_transaction(manager=None)
    def enable_trigger(
        cls,
        session,
        *,
        trigger_id: str,
    ) -> Dict[str, Any]:
        """
        Trigger'ı aktif eder.
        
        Args:
            trigger_id: Trigger ID'si
            
        Returns:
            {"success": True, "is_enabled": True}
        """
        trigger = cls._trigger_repo._get_by_id(session, record_id=trigger_id)
        
        if not trigger:
            raise ResourceNotFoundError(
                resource_name="Trigger",
                resource_id=trigger_id
            )
        
        if trigger.is_enabled:
            raise BusinessRuleViolationError(
                rule_name="already_enabled",
                rule_detail=f"Trigger {trigger_id} is already enabled",
                message="Trigger is already enabled"
            )
        
        cls._trigger_repo._update(
            session,
            record_id=trigger_id,
            is_enabled=True
        )
        
        return {"success": True, "is_enabled": True}

    @classmethod
    @with_transaction(manager=None)
    def disable_trigger(
        cls,
        session,
        *,
        trigger_id: str,
    ) -> Dict[str, Any]:
        """
        Trigger'ı devre dışı bırakır.
        
        Args:
            trigger_id: Trigger ID'si
            
        Returns:
            {"success": True, "is_enabled": False}
        """
        trigger = cls._trigger_repo._get_by_id(session, record_id=trigger_id)
        
        if not trigger:
            raise ResourceNotFoundError(
                resource_name="Trigger",
                resource_id=trigger_id
            )
        
        if not trigger.is_enabled:
            raise BusinessRuleViolationError(
                rule_name="already_disabled",
                rule_detail=f"Trigger {trigger_id} is already disabled",
                message="Trigger is already disabled"
            )
        
        cls._trigger_repo._update(
            session,
            record_id=trigger_id,
            is_enabled=False
        )
        
        return {"success": True, "is_enabled": False}

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_trigger(
        cls,
        session,
        *,
        trigger_id: str,
    ) -> Dict[str, Any]:
        """
        Trigger'ı siler.
        
        NOT: 
        - DEFAULT trigger silinemez.
        - Minimum trigger sayısı (varsayılan: 1) korunmalıdır.
        
        Args:
            trigger_id: Trigger ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        trigger = cls._trigger_repo._get_by_id(session, record_id=trigger_id)
        
        if not trigger:
            raise ResourceNotFoundError(
                resource_name="Trigger",
                resource_id=trigger_id
            )
        
        # DEFAULT trigger koruması
        if trigger.name == "DEFAULT":
            raise BusinessRuleViolationError(
                rule_name="cannot_delete_default",
                rule_detail=f"Trigger {trigger_id} is the DEFAULT trigger and cannot be deleted",
                message="Cannot delete the DEFAULT trigger"
            )
        
        # Minimum trigger sayısı kontrolü
        current_triggers = cls._trigger_repo._get_all_by_workflow_id(
            session, 
            workflow_id=trigger.workflow_id
        )
        current_trigger_count = len(current_triggers)
        
        if current_trigger_count <= cls._min_triggers_per_workflow:
            raise BusinessRuleViolationError(
                rule_name="minimum_triggers_required",
                rule_detail=f"Workflow {workflow_id} has {current_trigger_count} triggers, minimum required is {cls._min_triggers_per_workflow}",
                message=f"Cannot delete trigger. Workflow must have at least {cls._min_triggers_per_workflow} trigger(s)"
            )
        
        cls._trigger_repo._delete(session, record_id=trigger_id)
        
        return {
            "success": True,
            "deleted_id": trigger_id
        }
    
    # ==================================================================================== LIMITS INFO ==
    @classmethod
    def get_trigger_limits(cls) -> Dict[str, Any]:
        """
        Trigger limit bilgilerini getirir.
        
        Returns:
            {"min_triggers_per_workflow": int, "max_triggers_per_workflow": int}
        """
        return {
            "min_triggers_per_workflow": cls._min_triggers_per_workflow,
            "max_triggers_per_workflow": cls._max_triggers_per_workflow
        }

