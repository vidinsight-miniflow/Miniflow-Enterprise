from typing import Dict, Any, Optional, List
from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.models.enums import ExecutionStatus
from src.miniflow.database.utils.pagination_params import PaginationParams
from src.miniflow.database.utils.filter_params import FilterParams
from datetime import datetime, timezone
from src.miniflow.core.exceptions import ResourceNotFoundError, InvalidInputError



class ExecutionService:
    def __init__(self):
        self._registry = RepositoryRegistry()
        
        # Repositories
        self._execution_input_repo = self._registry.execution_input_repository
        self._execution_output_repo = self._registry.execution_output_repository
        self._execution_repo = self._registry.execution_repository
        self._variable_repo = self._registry.variable_repository
        self._credential_repo = self._registry.credential_repository
        self._database_repo = self._registry.database_repository
        self._file_repo = self._registry.file_repository
        self._node_repo = self._registry.node_repository
        self._edge_repo = self._registry.edge_repository
        self._workflow_repo = self._registry.workflow_repository
        self._script_repo = self._registry.script_repository
        self._custom_script_repo = self._registry.custom_script_repository
        self._trigger_repo = self._registry.trigger_repository

    #########################################################
    # Execution Başlatma Metotlari 
    #########################################################
    
    def _validate_trigger_input_data(
        self, 
        input_mapping: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> None:
        if input_mapping is None:
            raise InvalidInputError(
                field_name="input_mapping",
                message="Trigger input_mapping cannot be None"
            )
        
        if not isinstance(input_mapping, dict):
            raise InvalidInputError(
                field_name="input_mapping",
                message=f"Trigger input_mapping must be a dictionary, got {type(input_mapping).__name__}"
            )
        
        if not input_mapping:
            return  # No validation if input_mapping is empty
        
        if not isinstance(input_data, dict):
            raise InvalidInputError(
                field_name="trigger_data",
                message=f"Trigger data must be a dictionary, got {type(input_data).__name__}"
            )
        
        # Type string to Python type mapping (with aliases)
        type_map = {
            'str': str,
            'string': str,
            'int': int,
            'integer': int,
            'float': float,
            'number': float,
            'bool': bool,
            'boolean': bool,
            'dict': dict,
            'list': list,
            'tuple': tuple,
        }
        
        for key, mapping in input_mapping.items():
            if not isinstance(mapping, dict):
                raise InvalidInputError(
                    field_name=key,
                    message=f"Input mapping for '{key}' must be a dictionary, got {type(mapping).__name__}"
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

            # Type validation if type is specified
            if value is not None and type_str:
                if type_str not in type_map:
                    raise InvalidInputError(
                        field_name=key,
                        message=f"Unsupported type '{type_str}' for parameter '{key}'. Supported types: {', '.join(sorted(set(type_map.keys())))}"
                    )
                
                expected_type = type_map[type_str]
                if not isinstance(value, expected_type):
                    raise InvalidInputError(
                        field_name=key, 
                        message=f"Parameter '{key}' must be a {type_str}, got {type(value).__name__}"
                    )

    def _extract_node_parameters(
        self,
        node_params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:

        if node_params is None:
            raise InvalidInputError(
                field_name="input_params",
                message="Node input_params cannot be None"
            )
        
        if not isinstance(node_params, dict):
            raise InvalidInputError(
                field_name="input_params",
                message=f"Node input_params must be a dictionary, got {type(node_params).__name__}"
            )
        
        extracted = {}

        for key, meta in node_params.items():
            if not isinstance(meta, dict):
                raise InvalidInputError(
                    field_name=key,
                    message=f"Parameter '{key}' metadata must be a dictionary, got {type(meta).__name__}"
                )
            
            required = meta.get("required", False)
            value = meta.get("value", None)
            default_value = meta.get("default_value", None)
            type_str = meta.get("type", "string")

            if required and value is None:
                raise InvalidInputError(
                    field_name=key, 
                    message=f"Missing required value for field '{key}'"
                )

            if value is None:
                if default_value:
                    value = default_value
                else:
                    raise InvalidInputError(
                        field_name=key,
                        message=f"Missing required value for field '{key}'"
                    )

            extracted[key] = {
                'value': value,
                'type': type_str,
            }

        return extracted

    @with_transaction(manager=None)
    def start_execution(
        self,
        session,
        *,
        trigger_id: str,
        trigger_data: Dict[str, Any],
        triggered_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        trigger = self._trigger_repo._get_by_id(session, record_id=trigger_id, include_deleted=False)
        if not trigger:
            raise ResourceNotFoundError(resource_name="trigger", resource_id=trigger_id)

        if trigger.input_mapping:
            self._validate_trigger_input_data(trigger.input_mapping, trigger_data)
        
        workflow_id = trigger.workflow_id
        workspace_id = trigger.workspace_id
        
        execution_record = self._create_execution_record(
            session, 
            workspace_id=workspace_id, 
            workflow_id=workflow_id, 
            trigger_id=trigger_id, 
            trigger_data=trigger_data, 
            triggered_by=triggered_by
        )
        
        # execution_record bir dict döndürüyor, id'yi al
        execution_id = execution_record['id']

        execution_inputs = self._create_execution_inputs(
            session, 
            execution_id=execution_id, 
            workflow_id=workflow_id,
            workspace_id=workspace_id, 
            triggered_by=triggered_by
        )

        return {
            'id': execution_id,
            'started_at': execution_record['started_at'],
            'execution_inputs_count': len(execution_inputs),
            'execution_inputs': execution_inputs
        }

    def _create_execution_record(
        self,
        session,
        *,
        workspace_id: str,
        workflow_id: str,
        trigger_id: str,
        trigger_data: Dict[str, Any],
        triggered_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        execution = self._execution_repo._create(
            session,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            trigger_id=trigger_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            trigger_data=trigger_data,
            created_by=triggered_by,
        )

        return {
            'id': execution.id,
            'started_at': execution.started_at,
        }

    def _create_execution_inputs(
        self,
        session,
        *,
        execution_id: str,
        workflow_id: str,
        workspace_id: str,
        triggered_by: Optional[str] = None,
    ):
        
        nodes = self._node_repo._get_all_by_workflow_id(session, workflow_id=workflow_id, include_deleted=False)
        edges = self._edge_repo._get_all_by_workflow_id(session, workflow_id=workflow_id, include_deleted=False)

        dependency_map = {}
        for edge in edges:
            to_node_id = edge.to_node_id
            if to_node_id not in dependency_map:
                dependency_map[to_node_id] = []
            dependency_map[to_node_id].append(edge.from_node_id)
        
        # Batch olarak tüm script_id'leri topla
        script_ids = []
        custom_script_ids = []
        for node in nodes:
            if node.script_id:
                script_ids.append(node.script_id)
            elif node.custom_script_id:
                custom_script_ids.append(node.custom_script_id)
        
        # Batch olarak script'leri getir
        scripts_map = {}
        if script_ids:
            scripts = self._script_repo._get_by_ids(session, record_ids=script_ids, include_deleted=False)
            scripts_map = {script.id: script for script in scripts}
        
        custom_scripts_map = {}
        if custom_script_ids:
            custom_scripts = self._custom_script_repo._get_by_ids(session, record_ids=custom_script_ids, include_deleted=False)
            custom_scripts_map = {script.id: script for script in custom_scripts}
        
        execution_inputs = []
        for node in nodes:
            dependency_count = len(dependency_map.get(node.id, []))
            
            script_path = None
            script_name = None

            if node.script_id:
                script = scripts_map.get(node.script_id)
                if script:
                    script_name = script.name
                    script_path = script.file_path
            elif node.custom_script_id:
                script = custom_scripts_map.get(node.custom_script_id)
                if script:
                    script_name = script.name
                    script_path = script.file_path
            
            if not script_path:
                raise InvalidInputError(field_name="script_id", message="Node has no script")

            parameters = self._extract_node_parameters(node.input_params)
            
            node_name = node.name
            node_id = node.id

            execution_input = self._execution_input_repo._create(
                session,
                execution_id=execution_id,
                workflow_id=workflow_id,
                workspace_id=workspace_id,
                node_id=node_id,
                dependency_count=dependency_count,
                priority=node.workflow.priority if node.workflow else 0,
                max_retries=node.max_retries,
                timeout_seconds=node.timeout_seconds,
                node_name=node_name,
                params=parameters,
                script_name=script_name,
                script_path=script_path,
                created_by=triggered_by,
            )

            execution_inputs.append({
                    'id': execution_input.id,
                    'node_name': execution_input.node_name,
                    'dependency_count': execution_input.dependency_count
                })

        return execution_inputs
            
    #########################################################
    # Execution Bitirme Metotlari 
    #########################################################

    @with_transaction(manager=None)
    def end_execution(
        self,
        session,
        *,
        execution_id: str,
        status: ExecutionStatus,
    ):
        """Public API - yeni transaction oluşturur"""
        response = self._update_execution(session, execution_id=execution_id, status=status)
        return response
    
    def _end_execution(
        self,
        session,
        *,
        execution_id: str,
        status: ExecutionStatus,
    ):
        """Internal API - mevcut session'ı kullanır (transaction içinde çağrılabilir)"""
        response = self._update_execution(session, execution_id=execution_id, status=status)
        return response

    def _cleanup_execution_inputs(
        self,
        session,
        execution_id: str,
    ):
        remaining_inputs = self._execution_input_repo._get_by_execution_id(session, record_id=execution_id, include_deleted=False)
        self._execution_input_repo._delete_by_execution_id(session, execution_id=execution_id)

        return {
            'remaining_inputs_count': len(remaining_inputs),
            'remaining_inputs': [
                {
                    'id': input.id,
                    'node_name': input.node_name,
                    'node_id': input.node_id,
                } for input in remaining_inputs
            ],
        }

    def _cleanup_execution_outputs(
        self,
        session,
        execution_id: str,
    ):
        remaining_outputs = self._execution_output_repo._get_by_execution_id(session, record_id=execution_id, include_deleted=False)
        self._execution_output_repo._delete_by_execution_id(session, execution_id=execution_id)

        return {
            'remaining_outputs_count': len(remaining_outputs),
            'remaining_outputs': [
                {
                    'id': output.id,
                    'node_id': output.node_id,
                    'status': output.status,
                } for output in remaining_outputs
            ],
        }

    def _collect_execution_results(
        self,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """Collect execution results before cleanup"""
        remaining_inputs = self._execution_input_repo._get_by_execution_id(session, record_id=execution_id, include_deleted=False)
        outputs = self._execution_output_repo._get_by_execution_id(session, record_id=execution_id, include_deleted=False)

        final_dict = {}
        for output in outputs:
            final_dict[output.node_id] = {
                'status': output.status,
                'result_data': output.result_data,
                'memory_mb': output.memory_mb,
                'cpu_percent': output.cpu_percent,
                'duration_seconds': output.duration,
                'error_message': output.error_message,
                'error_details': output.error_details,
            }

        for input in remaining_inputs:
            final_dict[input.node_id] = {
                'status': ExecutionStatus.CANCELLED,
                'result_data': None,
                'memory_mb': None,
                'cpu_percent': None,
                'duration_seconds': None,
                'error_message': 'Execution cancelled',
                'error_details': 'Execution cancelled',
            }

        return final_dict

    def _update_execution(
        self,
        session,
        *,
        execution_id: str,
        status: ExecutionStatus,
    ):
        execution = self._execution_repo._get_by_id(session, record_id=execution_id, include_deleted=False)

        results = self._collect_execution_results(session, execution_id=execution_id)

        # Execution tamamlanırken tüm execution inputs ve outputs'ları temizle
        self._cleanup_execution_inputs(session, execution_id=execution_id)
        self._cleanup_execution_outputs(session, execution_id=execution_id)

        execution.status = status
        execution.ended_at = datetime.now(timezone.utc)
        execution.results = results

        return {
            'id': execution.id,
            'status': execution.status,
            'duration': execution.duration,
        }
    
    #########################################################
    # Execution Getirme Metotlari (FRONTEND)
    #########################################################

    def _get_execution_dict(self, execution) -> Dict[str, Any]:
        """Helper method to convert execution to dict"""
        return {
            "id": execution.id,
            "status": execution.status.value if execution.status else None,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "ended_at": execution.ended_at.isoformat() if execution.ended_at else None,
            "duration": execution.duration,
            "trigger_data": execution.trigger_data or {},
            "results": execution.results or {},
            "triggered_by": execution.created_by,
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
            "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
        }

    @with_readonly_session(manager=None)
    def get_execution_by_id(
        self,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """Get execution by ID"""
        execution = self._execution_repo._get_by_id(session, record_id=execution_id, include_deleted=False)
        if not execution:
            raise ResourceNotFoundError(resource_name="execution", resource_id=execution_id)
        
        return self._get_execution_dict(execution)

    @with_readonly_session(manager=None)
    def get_pending_execution_by_workspace_id(
        self,
        session,
        *,
        workspace_id: str,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """Get all pending executions for a workspace with pagination"""
        return self._get_executions_by_status(
            session,
            workspace_id=workspace_id,
            status=ExecutionStatus.PENDING,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc,
            include_deleted=include_deleted,
        )

    @with_readonly_session(manager=None)
    def get_running_execution_by_workspace_id(
        self,
        session,
        *,
        workspace_id: str,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """Get all running executions for a workspace with pagination"""
        return self._get_executions_by_status(
            session,
            workspace_id=workspace_id,
            status=ExecutionStatus.RUNNING,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc,
            include_deleted=include_deleted,
        )

    @with_readonly_session(manager=None)
    def get_completed_execution_by_workspace_id(
        self,
        session,
        *,
        workspace_id: str,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """Get all completed executions for a workspace with pagination"""
        return self._get_executions_by_status(
            session,
            workspace_id=workspace_id,
            status=ExecutionStatus.COMPLETED,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc,
            include_deleted=include_deleted,
        )

    @with_readonly_session(manager=None)
    def get_failed_execution_by_workspace_id(
        self,
        session,
        *,
        workspace_id: str,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """Get all failed executions for a workspace with pagination"""
        return self._get_executions_by_status(
            session,
            workspace_id=workspace_id,
            status=ExecutionStatus.FAILED,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc,
            include_deleted=include_deleted,
        )

    @with_readonly_session(manager=None)
    def get_cancelled_execution_by_workspace_id(
        self,
        session,
        *,
        workspace_id: str,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """Get all cancelled executions for a workspace with pagination"""
        return self._get_executions_by_status(
            session,
            workspace_id=workspace_id,
            status=ExecutionStatus.CANCELLED,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc,
            include_deleted=include_deleted,
        )

    def _get_executions_by_status(
        self,
        session,
        *,
        workspace_id: str,
        status: ExecutionStatus,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """Helper method to get executions by status with pagination"""
        pagination_params = PaginationParams(
            page=page,
            page_size=page_size,
            order_by=order_by or "created_at",
            order_desc=order_desc,
            include_deleted=include_deleted
        )
        pagination_params.validate()
        
        # Build filters
        filter_params = FilterParams()
        filter_params.add_equality_filter('workspace_id', workspace_id)
        filter_params.add_equality_filter('status', status)
        
        result = self._execution_repo._paginate(
            session,
            pagination_params=pagination_params,
            filter_params=filter_params
        )
        
        items = [self._get_execution_dict(execution) for execution in result.items]
        
        return {
            "items": items,
            "metadata": result.metadata.to_dict()
        }