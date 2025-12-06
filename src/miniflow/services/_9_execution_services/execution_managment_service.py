from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import ExecutionStatus
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
    InvalidInputError,
)


class ExecutionManagementService:
    """
    Execution yönetim servisi.
    
    Execution başlatma (trigger ile veya workflow ile), durdurma ve listeleme işlemlerini sağlar.
    
    Execution Başlatma Yöntemleri:
    1. Trigger ID ile (API): Trigger aktif mi kontrol edilir
    2. Workflow ID ile (UI Test): Kontrol mekanizması yok
    
    NOT: workspace_exists ve workflow_exists kontrolleri middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _execution_repo = _registry.execution_repository()
    _execution_input_repo = _registry.execution_input_repository()
    _execution_output_repo = _registry.execution_output_repository()
    _trigger_repo = _registry.trigger_repository()
    _workflow_repo = _registry.workflow_repository()
    _node_repo = _registry.node_repository()
    _edge_repo = _registry.edge_repository()
    _script_repo = _registry.script_repository()
    _custom_script_repo = _registry.custom_script_repository()

    # ==================================================================================== VALIDATION HELPERS ==
    @classmethod
    def _validate_trigger_input_data(
        cls,
        input_mapping: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> None:
        """Trigger input mapping'e göre input_data'yı validate eder."""
        if input_mapping is None or not input_mapping:
            return
        
        if not isinstance(input_mapping, dict):
            raise InvalidInputError(
                field_name="input_mapping",
                message="Trigger input_mapping must be a dictionary"
            )
        
        if not isinstance(input_data, dict):
            raise InvalidInputError(
                field_name="trigger_data",
                message="Trigger data must be a dictionary"
            )
        
        type_map = {
            'str': str, 'string': str,
            'int': int, 'integer': int,
            'float': float, 'number': float,
            'bool': bool, 'boolean': bool,
            'dict': dict, 'list': list,
        }
        
        for key, mapping in input_mapping.items():
            if not isinstance(mapping, dict):
                raise InvalidInputError(
                    field_name=key,
                    message=f"Input mapping for '{key}' must be a dictionary"
                )
            
            type_str = mapping.get("type", "").lower()
            default_value = mapping.get("value")
            required = mapping.get("required", False)
            
            if required and key not in input_data:
                raise InvalidInputError(
                    field_name=key,
                    message=f"Parameter '{key}' is required"
                )
            
            value = input_data.get(key, default_value)
            
            if value is not None and type_str:
                if type_str not in type_map:
                    raise InvalidInputError(
                        field_name=key,
                        message=f"Unsupported type '{type_str}' for parameter '{key}'"
                    )
                
                expected_type = type_map[type_str]
                if not isinstance(value, expected_type):
                    raise InvalidInputError(
                        field_name=key,
                        message=f"Parameter '{key}' must be a {type_str}"
                    )

    @classmethod
    def _extract_node_parameters(
        cls,
        node_params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Node parametrelerini çıkarır ve validate eder."""
        if node_params is None:
            return {}
        
        if not isinstance(node_params, dict):
            raise InvalidInputError(
                field_name="input_params",
                message="Node input_params must be a dictionary"
            )
        
        extracted = {}
        for key, meta in node_params.items():
            if not isinstance(meta, dict):
                raise InvalidInputError(
                    field_name=key,
                    message=f"Parameter '{key}' metadata must be a dictionary"
                )
            
            required = meta.get("required", False)
            value = meta.get("value")
            default_value = meta.get("default_value")
            type_str = meta.get("type", "string")
            
            if required and value is None:
                if default_value is not None:
                    value = default_value
                else:
                    raise InvalidInputError(
                        field_name=key,
                        message=f"Missing required value for field '{key}'"
                    )
            
            if value is None and default_value is not None:
                value = default_value
            
            extracted[key] = {
                'value': value,
                'type': type_str,
            }
        
        return extracted

    # ==================================================================================== START EXECUTION ==
    @classmethod
    @with_transaction(manager=None)
    def start_execution_by_trigger(
        cls,
        session,
        *,
        trigger_id: str,
        trigger_data: Dict[str, Any],
        triggered_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Trigger ID ile execution başlatır (API üzerinden).
        
        - Trigger'ın aktif olup olmadığı kontrol edilir
        - Trigger'ın input_mapping'ine göre trigger_data validate edilir
        - Workflow'un tüm node'ları için ExecutionInput oluşturulur
        
        Args:
            trigger_id: Trigger ID'si
            trigger_data: Trigger'a gönderilen veri
            triggered_by: Tetikleyen kullanıcı ID'si (opsiyonel)
            
        Returns:
            {"id": str, "started_at": str, "execution_inputs_count": int}
        """
        # Trigger kontrolü
        trigger = cls._trigger_repo._get_by_id(session, record_id=trigger_id)
        if not trigger:
            raise ResourceNotFoundError(
                resource_name="Trigger",
                resource_id=trigger_id
            )
        
        # Trigger aktif mi?
        if not trigger.is_enabled:
            raise BusinessRuleViolationError(
                rule_name="trigger_disabled",
                rule_detail=f"Trigger {trigger_id} is disabled",
                message="Trigger is disabled"
            )
        
        # Input mapping validation
        if trigger.input_mapping:
            cls._validate_trigger_input_data(trigger.input_mapping, trigger_data)
        
        workflow_id = trigger.workflow_id
        workspace_id = trigger.workspace_id
        
        # Execution oluştur
        execution = cls._execution_repo._create(
            session,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            trigger_id=trigger_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            trigger_data=trigger_data,
            created_by=triggered_by
        )
        
        # Execution inputs oluştur
        execution_inputs = cls._create_execution_inputs(
            session,
            execution_id=execution.id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            triggered_by=triggered_by
        )
        
        return {
            "id": execution.id,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "execution_inputs_count": len(execution_inputs)
        }

    @classmethod
    @with_transaction(manager=None)
    def start_execution_by_workflow(
        cls,
        session,
        *,
        workspace_id: str,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workflow ID ile execution başlatır (UI test için).
        
        - Herhangi bir kontrol mekanizması YOK (test amaçlı)
        - Trigger ID olmadan execution oluşturulur
        
        Args:
            workspace_id: Workspace ID'si
            workflow_id: Workflow ID'si
            input_data: Test verisi (opsiyonel)
            triggered_by: Tetikleyen kullanıcı ID'si (opsiyonel)
            
        Returns:
            {"id": str, "started_at": str, "execution_inputs_count": int}
        """
        # Execution oluştur (trigger_id = None)
        execution = cls._execution_repo._create(
            session,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            trigger_id=None,
            status=ExecutionStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            trigger_data=input_data or {},
            created_by=triggered_by
        )
        
        # Execution inputs oluştur
        execution_inputs = cls._create_execution_inputs(
            session,
            execution_id=execution.id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            triggered_by=triggered_by
        )
        
        return {
            "id": execution.id,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "execution_inputs_count": len(execution_inputs)
        }

    @classmethod
    def _create_execution_inputs(
        cls,
        session,
        *,
        execution_id: str,
        workflow_id: str,
        workspace_id: str,
        triggered_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Workflow'un tüm node'ları için ExecutionInput oluşturur.
        """
        nodes = cls._node_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        edges = cls._edge_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        
        if not nodes:
            raise BusinessRuleViolationError(
                rule_name="no_nodes",
                rule_detail=f"Workflow {workflow_id} has no nodes",
                message="Workflow has no nodes"
            )
        
        # Dependency map oluştur
        dependency_map = {}
        for edge in edges:
            to_node_id = edge.to_node_id
            if to_node_id not in dependency_map:
                dependency_map[to_node_id] = []
            dependency_map[to_node_id].append(edge.from_node_id)
        
        # Script'leri batch olarak getir
        script_ids = [n.script_id for n in nodes if n.script_id]
        custom_script_ids = [n.custom_script_id for n in nodes if n.custom_script_id]
        
        scripts_map = {}
        if script_ids:
            scripts = cls._script_repo._get_by_ids(session, record_ids=script_ids)
            scripts_map = {s.id: s for s in scripts}
        
        custom_scripts_map = {}
        if custom_script_ids:
            custom_scripts = cls._custom_script_repo._get_by_ids(session, record_ids=custom_script_ids)
            custom_scripts_map = {s.id: s for s in custom_scripts}
        
        # Workflow'un priority'sini al
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        workflow_priority = workflow.priority if workflow else 0
        
        execution_inputs = []
        for node in nodes:
            dependency_count = len(dependency_map.get(node.id, []))
            
            # Script bilgilerini al
            script = None
            if node.script_id:
                script = scripts_map.get(node.script_id)
            elif node.custom_script_id:
                script = custom_scripts_map.get(node.custom_script_id)
            
            if not script or not script.file_path:
                raise InvalidInputError(
                    field_name="script_id",
                    message=f"Node '{node.name}' has no valid script"
                )
            
            # Node parametrelerini çıkar
            parameters = cls._extract_node_parameters(node.input_params)
            
            # ExecutionInput oluştur
            execution_input = cls._execution_input_repo._create(
                session,
                execution_id=execution_id,
                workflow_id=workflow_id,
                workspace_id=workspace_id,
                node_id=node.id,
                dependency_count=dependency_count,
                priority=workflow_priority,
                max_retries=node.max_retries,
                timeout_seconds=node.timeout_seconds,
                node_name=node.name,
                params=parameters,
                script_name=script.name,
                script_path=script.file_path,
                created_by=triggered_by
            )
            
            execution_inputs.append({
                "id": execution_input.id,
                "node_name": execution_input.node_name,
                "dependency_count": execution_input.dependency_count
            })
        
        return execution_inputs

    # ==================================================================================== END EXECUTION ==
    @classmethod
    @with_transaction(manager=None)
    def end_execution(
        cls,
        session,
        *,
        execution_id: str,
        status: ExecutionStatus,
    ) -> Dict[str, Any]:
        """
        Execution'ı sonlandırır.
        
        - Execution sonuçlarını toplar
        - ExecutionInput ve ExecutionOutput'ları temizler
        - Execution durumunu günceller
        
        Args:
            execution_id: Execution ID'si
            status: Final durum (COMPLETED, FAILED, CANCELLED, TIMEOUT)
            
        Returns:
            {"id": str, "status": str, "duration": float}
        """
        execution = cls._execution_repo._get_by_id(session, record_id=execution_id)
        
        if not execution:
            raise ResourceNotFoundError(
                resource_name="Execution",
                resource_id=execution_id
            )
        
        # Sonuçları topla
        results = cls._collect_execution_results(session, execution_id=execution_id)
        
        # Cleanup
        cls._execution_input_repo._delete_by_execution_id(session, execution_id=execution_id)
        cls._execution_output_repo._delete_by_execution_id(session, execution_id=execution_id)
        
        # Execution'ı güncelle
        ended_at = datetime.now(timezone.utc)
        cls._execution_repo._update_status(
            session,
            execution_id=execution_id,
            status=status,
            ended_at=ended_at,
            results=results
        )
        
        # Duration hesapla
        duration = None
        if execution.started_at:
            delta = ended_at - execution.started_at
            duration = delta.total_seconds()
        
        return {
            "id": execution_id,
            "status": status.value,
            "duration": duration
        }

    @classmethod
    def _collect_execution_results(
        cls,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """Execution sonuçlarını toplar."""
        remaining_inputs = cls._execution_input_repo._get_by_execution_id(
            session, 
            record_id=execution_id
        )
        outputs = cls._execution_output_repo._get_by_execution_id(
            session, 
            record_id=execution_id
        )
        
        results = {}
        
        # Output'lardan sonuçları al
        for output in outputs:
            results[output.node_id] = {
                "status": output.status,
                "result_data": output.result_data,
                "duration": output.duration,
                "error_message": output.error_message,
                "error_details": output.error_details
            }
        
        # Bekleyen input'ları CANCELLED olarak işaretle
        for inp in remaining_inputs:
            if inp.node_id not in results:
                results[inp.node_id] = {
                    "status": "CANCELLED",
                    "result_data": None,
                    "duration": None,
                    "error_message": "Execution cancelled",
                    "error_details": None
                }
        
        return results

    @classmethod
    @with_transaction(manager=None)
    def cancel_execution(
        cls,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Execution'ı iptal eder.
        
        Args:
            execution_id: Execution ID'si
            
        Returns:
            {"success": True, "id": str, "status": "CANCELLED"}
        """
        execution = cls._execution_repo._get_by_id(session, record_id=execution_id)
        
        if not execution:
            raise ResourceNotFoundError(
                resource_name="Execution",
                resource_id=execution_id
            )
        
        # Zaten tamamlanmış mı?
        if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, 
                                 ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]:
            raise BusinessRuleViolationError(
                rule_name="execution_already_finished",
                rule_detail=f"Execution {execution_id} is already {execution.status.value}",
                message=f"Execution is already {execution.status.value}"
            )
        
        return cls.end_execution(session, execution_id=execution_id, status=ExecutionStatus.CANCELLED)

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_execution(
        cls,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Execution detaylarını getirir.
        
        Args:
            execution_id: Execution ID'si
            
        Returns:
            Execution detayları
        """
        execution = cls._execution_repo._get_by_id(session, record_id=execution_id)
        
        if not execution:
            raise ResourceNotFoundError(
                resource_name="Execution",
                resource_id=execution_id
            )
        
        return {
            "id": execution.id,
            "workspace_id": execution.workspace_id,
            "workflow_id": execution.workflow_id,
            "trigger_id": execution.trigger_id,
            "status": execution.status.value if execution.status else None,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "ended_at": execution.ended_at.isoformat() if execution.ended_at else None,
            "duration": execution.duration,
            "trigger_data": execution.trigger_data or {},
            "results": execution.results or {},
            "retry_count": execution.retry_count,
            "max_retries": execution.max_retries,
            "is_retry": execution.is_retry,
            "triggered_by": execution.created_by,
            "created_at": execution.created_at.isoformat() if execution.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_executions(
        cls,
        session,
        *,
        workspace_id: str,
        status: Optional[ExecutionStatus] = None,
    ) -> Dict[str, Any]:
        """
        Workspace'in execution'larını listeler.
        
        Args:
            workspace_id: Workspace ID'si
            status: Durum filtresi (opsiyonel)
            
        Returns:
            {"workspace_id": str, "executions": List[Dict], "count": int}
        """
        if status:
            executions = cls._execution_repo._get_by_status(
                session,
                workspace_id=workspace_id,
                status=status
            )
        else:
            executions = cls._execution_repo._get_all_by_workspace_id(
                session,
                workspace_id=workspace_id
            )
        
        return {
            "workspace_id": workspace_id,
            "executions": [
                {
                    "id": e.id,
                    "workflow_id": e.workflow_id,
                    "trigger_id": e.trigger_id,
                    "status": e.status.value if e.status else None,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "ended_at": e.ended_at.isoformat() if e.ended_at else None,
                    "duration": e.duration
                }
                for e in executions
            ],
            "count": len(executions)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workflow_executions(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'un execution'larını listeler.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"workflow_id": str, "executions": List[Dict], "count": int}
        """
        executions = cls._execution_repo._get_all_by_workflow_id(
            session,
            workflow_id=workflow_id
        )
        
        return {
            "workflow_id": workflow_id,
            "executions": [
                {
                    "id": e.id,
                    "trigger_id": e.trigger_id,
                    "status": e.status.value if e.status else None,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "ended_at": e.ended_at.isoformat() if e.ended_at else None,
                    "duration": e.duration
                }
                for e in executions
            ],
            "count": len(executions)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_execution_stats(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace için execution istatistiklerini getirir.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {"total": int, "pending": int, "running": int, "completed": int, "failed": int}
        """
        total = cls._execution_repo._count_by_workspace_id(session, workspace_id=workspace_id)
        pending = cls._execution_repo._count_by_status(
            session, workspace_id=workspace_id, status=ExecutionStatus.PENDING
        )
        running = cls._execution_repo._count_by_status(
            session, workspace_id=workspace_id, status=ExecutionStatus.RUNNING
        )
        completed = cls._execution_repo._count_by_status(
            session, workspace_id=workspace_id, status=ExecutionStatus.COMPLETED
        )
        failed = cls._execution_repo._count_by_status(
            session, workspace_id=workspace_id, status=ExecutionStatus.FAILED
        )
        cancelled = cls._execution_repo._count_by_status(
            session, workspace_id=workspace_id, status=ExecutionStatus.CANCELLED
        )
        
        return {
            "workspace_id": workspace_id,
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled
        }

