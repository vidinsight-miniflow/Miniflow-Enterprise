from typing import Optional, Dict, Any, List

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import WorkflowStatus, TriggerType
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)


class WorkflowManagementService:
    """
    Workflow yönetim servisi.
    
    Workflow CRUD işlemleri ve durum yönetimini sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _workflow_repo = _registry.workflow_repository()
    _workspace_repo = _registry.workspace_repository()
    _trigger_repo = _registry.trigger_repository()
    _node_repo = _registry.node_repository()
    _edge_repo = _registry.edge_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_workflow(
        cls,
        session,
        *,
        workspace_id: str,
        name: str,
        created_by: str,
        description: Optional[str] = None,
        priority: int = 1,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Yeni workflow oluşturur.
        
        - Workspace workflow limiti kontrol edilir
        - Varsayılan olarak DRAFT durumunda oluşturulur
        - Otomatik olarak DEFAULT API trigger oluşturulur
        
        Args:
            workspace_id: Workspace ID'si
            name: Workflow adı (workspace içinde benzersiz)
            created_by: Oluşturan kullanıcı ID'si
            description: Açıklama (opsiyonel)
            priority: Öncelik (varsayılan: 1)
            tags: Etiketler (opsiyonel)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Workflow name cannot be empty"
            )
        
        if priority < 1:
            raise InvalidInputError(
                field_name="priority",
                message="Priority must be greater than 0"
            )
        
        # Workspace kontrolü
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Limit kontrolü
        if workspace.current_workflow_count >= workspace.workflow_limit:
            raise BusinessRuleViolationError(
                rule_name="workflow_limit_reached",
                rule_detail=f"Workspace {workspace_id} has {workspace.current_workflow_count} workflows, limit is {workspace.workflow_limit}",
                message=f"Workflow limit reached. Maximum: {workspace.workflow_limit}"
            )
        
        # Benzersizlik kontrolü
        existing = cls._workflow_repo._get_by_name(
            session,
            workspace_id=workspace_id,
            name=name
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Workflow",
                conflicting_field="name",
                message=f"Workflow with name '{name}' already exists in workspace {workspace_id}"
            )
        
        # Workflow oluştur
        workflow = cls._workflow_repo._create(
            session,
            workspace_id=workspace_id,
            name=name,
            description=description,
            priority=priority,
            status=WorkflowStatus.DRAFT,
            status_message="Workflow created, awaiting configuration",
            tags=tags or [],
            created_by=created_by
        )
        
        # Default API trigger oluştur
        cls._trigger_repo._create(
            session,
            workspace_id=workspace_id,
            workflow_id=workflow.id,
            name="DEFAULT",
            trigger_type=TriggerType.WEBHOOK,
            config={},
            description="Default API trigger created automatically with workflow",
            input_mapping={},
            is_enabled=True,
            created_by=created_by
        )
        
        # Workspace workflow sayısını güncelle
        cls._workspace_repo._update(
            session,
            record_id=workspace_id,
            current_workflow_count=workspace.current_workflow_count + 1
        )
        
        return {"id": workflow.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_workflow(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow detaylarını getirir.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            Workflow detayları
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        # Node ve edge sayılarını al
        node_count = cls._node_repo._count_by_workflow_id(session, workflow_id=workflow_id)
        edge_count = cls._edge_repo._count_by_workflow_id(session, workflow_id=workflow_id)
        
        return {
            "id": workflow.id,
            "workspace_id": workflow.workspace_id,
            "name": workflow.name,
            "description": workflow.description,
            "priority": workflow.priority,
            "status": workflow.status.value if workflow.status else None,
            "status_message": workflow.status_message,
            "tags": workflow.tags or [],
            "node_count": node_count,
            "edge_count": edge_count,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "created_by": workflow.created_by
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_workflows(
        cls,
        session,
        *,
        workspace_id: str,
        status: Optional[WorkflowStatus] = None,
    ) -> Dict[str, Any]:
        """
        Workspace'in workflow'larını listeler.
        
        Args:
            workspace_id: Workspace ID'si
            status: Durum filtresi (opsiyonel)
            
        Returns:
            {"workspace_id": str, "workflows": List[Dict], "count": int}
        """
        if status:
            workflows = cls._workflow_repo._get_by_status(
                session,
                workspace_id=workspace_id,
                status=status
            )
        else:
            workflows = cls._workflow_repo._get_all_by_workspace_id(
                session,
                workspace_id=workspace_id
            )
        
        return {
            "workspace_id": workspace_id,
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "priority": w.priority,
                    "status": w.status.value if w.status else None,
                    "tags": w.tags or [],
                    "created_at": w.created_at.isoformat() if w.created_at else None
                }
                for w in workflows
            ],
            "count": len(workflows)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_workflow(
        cls,
        session,
        *,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Workflow bilgilerini günceller.
        
        Args:
            workflow_id: Workflow ID'si
            name: Yeni ad (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            priority: Yeni öncelik (opsiyonel)
            tags: Yeni etiketler (opsiyonel)
            
        Returns:
            Güncellenmiş workflow bilgileri
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        # Validasyonlar
        if name is not None:
            if not name.strip():
                raise InvalidInputError(
                    field_name="name",
                    message="Workflow name cannot be empty"
                )
            # İsim değişikliği için benzersizlik kontrolü
            if name != workflow.name:
                existing = cls._workflow_repo._get_by_name(
                    session,
                    workspace_id=workflow.workspace_id,
                    name=name
                )
                if existing:
                    raise ResourceAlreadyExistsError(
                        resource_name="Workflow",
                        conflicting_field="name",
                        message=f"Workflow with name '{name}' already exists in workspace {workspace_id}"
                    )
        
        if priority is not None and priority < 1:
            raise InvalidInputError(
                field_name="priority",
                message="Priority must be greater than 0"
            )
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if priority is not None:
            update_data["priority"] = priority
        if tags is not None:
            update_data["tags"] = tags
        
        if update_data:
            cls._workflow_repo._update(session, record_id=workflow_id, **update_data)
        
        return cls.get_workflow(session, workflow_id=workflow_id)

    # ==================================================================================== STATUS MANAGEMENT ==
    @classmethod
    @with_transaction(manager=None)
    def activate_workflow(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'u aktif eder.
        
        NOT: Workflow'da en az bir node olmalıdır.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"success": True, "status": "ACTIVE"}
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        if workflow.status == WorkflowStatus.ACTIVE:
            raise BusinessRuleViolationError(
                rule_name="already_active",
                rule_detail=f"Workflow {workflow_id} is already in ACTIVE status",
                message="Workflow is already active"
            )
        
        # Node kontrolü
        node_count = cls._node_repo._count_by_workflow_id(session, workflow_id=workflow_id)
        if node_count == 0:
            raise BusinessRuleViolationError(
                rule_name="no_nodes",
                rule_detail=f"Workflow {workflow_id} has no nodes (count: {node_count})",
                message="Workflow must have at least one node to be activated"
            )
        
        # Workflow'u aktif et
        cls._workflow_repo._update_status(
            session,
            workflow_id=workflow_id,
            status=WorkflowStatus.ACTIVE,
            status_message="Workflow is active and ready to execute"
        )
        
        # Tüm trigger'ları aktif et
        triggers = cls._trigger_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        for trigger in triggers:
            if not trigger.is_enabled:
                cls._trigger_repo._update(
                    session,
                    record_id=trigger.id,
                    is_enabled=True
                )
        
        return {"success": True, "status": "ACTIVE"}

    @classmethod
    @with_transaction(manager=None)
    def deactivate_workflow(
        cls,
        session,
        *,
        workflow_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workflow'u devre dışı bırakır.
        
        Args:
            workflow_id: Workflow ID'si
            reason: Devre dışı bırakma nedeni (opsiyonel)
            
        Returns:
            {"success": True, "status": "DEACTIVATED"}
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        if workflow.status == WorkflowStatus.DEACTIVATED:
            raise BusinessRuleViolationError(
                rule_name="already_deactivated",
                message="Workflow is already deactivated"
            )
        
        # Workflow'u deaktif et
        cls._workflow_repo._update_status(
            session,
            workflow_id=workflow_id,
            status=WorkflowStatus.DEACTIVATED,
            status_message=reason or "Workflow has been deactivated"
        )
        
        # Tüm trigger'ları deaktif et
        triggers = cls._trigger_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        for trigger in triggers:
            if trigger.is_enabled:
                cls._trigger_repo._update(
                    session,
                    record_id=trigger.id,
                    is_enabled=False
                )
        
        return {"success": True, "status": "DEACTIVATED"}

    @classmethod
    @with_transaction(manager=None)
    def archive_workflow(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'u arşivler.
        
        NOT: Arşivlenen workflow'lar aktif edilemez.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"success": True, "status": "ARCHIVED"}
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        if workflow.status == WorkflowStatus.ARCHIVED:
            raise BusinessRuleViolationError(
                rule_name="already_archived",
                rule_detail=f"Workflow {workflow_id} is already in ARCHIVED status",
                message="Workflow is already archived"
            )
        
        cls._workflow_repo._update_status(
            session,
            workflow_id=workflow_id,
            status=WorkflowStatus.ARCHIVED,
            status_message="Workflow has been archived"
        )
        
        return {"success": True, "status": "ARCHIVED"}

    @classmethod
    @with_transaction(manager=None)
    def set_draft(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'u draft durumuna getirir.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"success": True, "status": "DRAFT"}
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        if workflow.status == WorkflowStatus.ARCHIVED:
            raise BusinessRuleViolationError(
                rule_name="archived_workflow",
                rule_detail=f"Workflow {workflow_id} is archived and cannot be modified",
                message="Archived workflows cannot be modified"
            )
        
        cls._workflow_repo._update_status(
            session,
            workflow_id=workflow_id,
            status=WorkflowStatus.DRAFT,
            status_message="Workflow is in draft mode"
        )
        
        return {"success": True, "status": "DRAFT"}

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_workflow(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'u siler (cascade ile node, edge, trigger'lar da silinir).
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        workspace_id = workflow.workspace_id
        
        # Cascade delete - Model'de cascade="all, delete-orphan" tanımlı olsa da
        # Soft delete kullanıldığında manuel silmek gerekebilir
        cls._trigger_repo._delete_all_by_workflow_id(session, workflow_id=workflow_id)
        cls._edge_repo._delete_all_by_workflow_id(session, workflow_id=workflow_id)
        cls._node_repo._delete_all_by_workflow_id(session, workflow_id=workflow_id)
        
        # Workflow'u sil
        cls._workflow_repo._delete(session, record_id=workflow_id)
        
        # Workspace workflow sayısını güncelle
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if workspace:
            cls._workspace_repo._update(
                session,
                record_id=workspace_id,
                current_workflow_count=max(0, workspace.current_workflow_count - 1)
            )
        
        return {
            "success": True,
            "deleted_id": workflow_id
        }

    # ==================================================================================== GRAPH INFO ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_workflow_graph(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'un node ve edge grafiğini getirir.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"workflow_id": str, "nodes": List[Dict], "edges": List[Dict]}
        """
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        nodes = cls._node_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        edges = cls._edge_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "status": workflow.status.value if workflow.status else None,
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "description": n.description,
                    "script_id": n.script_id,
                    "custom_script_id": n.custom_script_id,
                    "script_type": "GLOBAL" if n.script_id else "CUSTOM" if n.custom_script_id else None,
                    "max_retries": n.max_retries,
                    "timeout_seconds": n.timeout_seconds,
                    "meta_data": n.meta_data
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "from_node_id": e.from_node_id,
                    "to_node_id": e.to_node_id
                }
                for e in edges
            ]
        }

