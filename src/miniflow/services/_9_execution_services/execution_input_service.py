"""
ExecutionInputService - Frontend için Execution Input bilgi servisi

Bu servis sadece READ-ONLY operasyonlar sağlar.
Frontend arayüzünde execution input'larını görüntülemek için kullanılır.

NOT: Tüm write operasyonları (update, delete, dependency yönetimi)
SchedulerForInputHandler tarafından yapılır (_0_internal_services/scheduler_service.py).
"""

from typing import Dict, Any, List

from miniflow.database import RepositoryRegistry, with_readonly_session
from miniflow.core.exceptions import ResourceNotFoundError


class ExecutionInputService:
    """
    Execution Input bilgi servisi (Frontend için).
    
    Sadece okuma operasyonları sağlar:
    - Execution input detayları
    - Execution'a ait input listesi
    - İstatistikler
    
    Write operasyonları için: SchedulerForInputHandler
    """
    _registry = RepositoryRegistry()
    _execution_input_repo = _registry.execution_input_repository()

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_execution_input(
        cls,
        session,
        *,
        input_id: str,
    ) -> Dict[str, Any]:
        """
        ExecutionInput detaylarını getirir.
        
        Args:
            input_id: ExecutionInput ID'si
            
        Returns:
            ExecutionInput detayları
        """
        execution_input = cls._execution_input_repo._get_by_id(session, record_id=input_id)
        
        if not execution_input:
            raise ResourceNotFoundError(
                resource_name="ExecutionInput",
                resource_id=input_id
            )
        
        return {
            "id": execution_input.id,
            "execution_id": execution_input.execution_id,
            "workflow_id": execution_input.workflow_id,
            "workspace_id": execution_input.workspace_id,
            "node_id": execution_input.node_id,
            "node_name": execution_input.node_name,
            "script_name": execution_input.script_name,
            "script_path": execution_input.script_path,
            "dependency_count": execution_input.dependency_count,
            "priority": execution_input.priority,
            "wait_factor": execution_input.wait_factor,
            "params": execution_input.params or {},
            "max_retries": execution_input.max_retries,
            "timeout_seconds": execution_input.timeout_seconds,
            "retry_count": execution_input.retry_count,
            "resource_retry_count": execution_input.resource_retry_count,
            "last_rejection_reason": execution_input.last_rejection_reason,
            "created_at": execution_input.created_at.isoformat() if execution_input.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_execution_inputs(
        cls,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Bir execution'ın tüm input'larını getirir.
        
        Args:
            execution_id: Execution ID'si
            
        Returns:
            {"execution_id": str, "inputs": List[Dict], "count": int}
        """
        inputs = cls._execution_input_repo._get_by_execution_id(
            session, 
            record_id=execution_id
        )
        
        return {
            "execution_id": execution_id,
            "inputs": [
                {
                    "id": inp.id,
                    "node_id": inp.node_id,
                    "node_name": inp.node_name,
                    "dependency_count": inp.dependency_count,
                    "priority": inp.priority,
                    "wait_factor": inp.wait_factor,
                    "retry_count": inp.retry_count,
                    "resource_retry_count": inp.resource_retry_count,
                    "max_retries": inp.max_retries,
                    "last_rejection_reason": inp.last_rejection_reason
                }
                for inp in inputs
            ],
            "count": len(inputs)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_pending_inputs_count(
        cls,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Bir execution'ın bekleyen input sayısını getirir.
        
        Args:
            execution_id: Execution ID'si
            
        Returns:
            {"execution_id": str, "pending_count": int, "ready_count": int}
        """
        inputs = cls._execution_input_repo._get_by_execution_id(
            session, 
            record_id=execution_id
        )
        
        pending_count = sum(1 for inp in inputs if inp.dependency_count > 0)
        ready_count = sum(1 for inp in inputs if inp.dependency_count == 0)
        
        return {
            "execution_id": execution_id,
            "pending_count": pending_count,
            "ready_count": ready_count,
            "total": len(inputs)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_input_by_node(
        cls,
        session,
        *,
        execution_id: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Belirli bir node'un execution input'unu getirir.
        
        Args:
            execution_id: Execution ID'si
            node_id: Node ID'si
            
        Returns:
            ExecutionInput detayları
        """
        execution_input = cls._execution_input_repo._get_by_execution_and_node(
            session,
            execution_id=execution_id,
            node_id=node_id
        )
        
        if not execution_input:
            raise ResourceNotFoundError(
                resource_name="ExecutionInput",
                resource_id=f"{execution_id}/{node_id}"
            )
        
        return {
            "id": execution_input.id,
            "execution_id": execution_input.execution_id,
            "node_id": execution_input.node_id,
            "node_name": execution_input.node_name,
            "dependency_count": execution_input.dependency_count,
            "priority": execution_input.priority,
            "wait_factor": execution_input.wait_factor,
            "params": execution_input.params or {},
            "max_retries": execution_input.max_retries,
            "timeout_seconds": execution_input.timeout_seconds,
            "retry_count": execution_input.retry_count,
            "resource_retry_count": execution_input.resource_retry_count,
            "last_rejection_reason": execution_input.last_rejection_reason
        }
