"""
ExecutionOutputService - Frontend için Execution Output bilgi servisi

Bu servis sadece READ-ONLY operasyonlar sağlar.
Frontend arayüzünde execution output'larını görüntülemek için kullanılır.

NOT: Tüm write operasyonları (create, update, status değişiklikleri)
SchedulerForOutputHandler tarafından yapılır (_0_internal_services/scheduler_service.py).
"""

from typing import Dict, Any, List

from miniflow.database import RepositoryRegistry, with_readonly_session
from miniflow.core.exceptions import ResourceNotFoundError


class ExecutionOutputService:
    """
    Execution Output bilgi servisi (Frontend için).
    
    Sadece okuma operasyonları sağlar:
    - Execution output detayları
    - Execution'a ait output listesi
    - Node bazlı output sorgulama
    - İstatistikler
    
    Write operasyonları için: SchedulerForOutputHandler
    """
    _registry = RepositoryRegistry()
    _execution_output_repo = _registry.execution_output_repository()

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_execution_output(
        cls,
        session,
        *,
        output_id: str,
    ) -> Dict[str, Any]:
        """
        ExecutionOutput detaylarını getirir.
        
        Args:
            output_id: ExecutionOutput ID'si
            
        Returns:
            ExecutionOutput detayları
        """
        output = cls._execution_output_repo._get_by_id(session, record_id=output_id)
        
        if not output:
            raise ResourceNotFoundError(
                resource_name="ExecutionOutput",
                resource_id=output_id
            )
        
        return {
            "id": output.id,
            "execution_id": output.execution_id,
            "workflow_id": output.workflow_id,
            "workspace_id": output.workspace_id,
            "node_id": output.node_id,
            "status": output.status,
            "result_data": output.result_data or {},
            "started_at": output.started_at.isoformat() if output.started_at else None,
            "ended_at": output.ended_at.isoformat() if output.ended_at else None,
            "duration": output.duration,
            "memory_mb": output.memory_mb,
            "cpu_percent": output.cpu_percent,
            "error_message": output.error_message,
            "error_details": output.error_details,
            "retry_count": output.retry_count,
            "execution_metadata": output.execution_metadata or {},
            "created_at": output.created_at.isoformat() if output.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_execution_outputs(
        cls,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Bir execution'ın tüm output'larını getirir.
        
        Args:
            execution_id: Execution ID'si
            
        Returns:
            {"execution_id": str, "outputs": List[Dict], "count": int}
        """
        outputs = cls._execution_output_repo._get_by_execution_id(
            session, 
            record_id=execution_id
        )
        
        return {
            "execution_id": execution_id,
            "outputs": [
                {
                    "id": out.id,
                    "node_id": out.node_id,
                    "status": out.status,
                    "duration": out.duration,
                    "started_at": out.started_at.isoformat() if out.started_at else None,
                    "ended_at": out.ended_at.isoformat() if out.ended_at else None,
                    "error_message": out.error_message,
                    "retry_count": out.retry_count
                }
                for out in outputs
            ],
            "count": len(outputs)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_output_by_node(
        cls,
        session,
        *,
        execution_id: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Belirli bir node'un execution output'unu getirir.
        
        Args:
            execution_id: Execution ID'si
            node_id: Node ID'si
            
        Returns:
            ExecutionOutput detayları
        """
        output = cls._execution_output_repo._get_by_execution_and_node(
            session,
            execution_id=execution_id,
            node_id=node_id
        )
        
        if not output:
            raise ResourceNotFoundError(
                resource_name="ExecutionOutput",
                resource_id=f"{execution_id}/{node_id}"
            )
        
        return {
            "id": output.id,
            "execution_id": output.execution_id,
            "node_id": output.node_id,
            "status": output.status,
            "result_data": output.result_data or {},
            "started_at": output.started_at.isoformat() if output.started_at else None,
            "ended_at": output.ended_at.isoformat() if output.ended_at else None,
            "duration": output.duration,
            "memory_mb": output.memory_mb,
            "cpu_percent": output.cpu_percent,
            "error_message": output.error_message,
            "error_details": output.error_details
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_outputs_by_status(
        cls,
        session,
        *,
        execution_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """
        Belirli bir duruma göre execution output'larını getirir.
        
        Args:
            execution_id: Execution ID'si
            status: Durum filtresi (PENDING, RUNNING, SUCCESS, FAILED, TIMEOUT, SKIPPED)
            
        Returns:
            {"execution_id": str, "status": str, "outputs": List[Dict], "count": int}
        """
        outputs = cls._execution_output_repo._get_by_status(
            session,
            execution_id=execution_id,
            status=status
        )
        
        return {
            "execution_id": execution_id,
            "status": status,
            "outputs": [
                {
                    "id": out.id,
                    "node_id": out.node_id,
                    "duration": out.duration,
                    "error_message": out.error_message
                }
                for out in outputs
            ],
            "count": len(outputs)
        }

    # ==================================================================================== STATS ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_execution_output_stats(
        cls,
        session,
        *,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Execution output istatistiklerini getirir.
        
        Args:
            execution_id: Execution ID'si
            
        Returns:
            {"total": int, "pending": int, "running": int, "success": int, "failed": int, ...}
        """
        total = cls._execution_output_repo._count_by_execution_id(
            session, execution_id=execution_id
        )
        pending = cls._execution_output_repo._count_by_status(
            session, execution_id=execution_id, status="PENDING"
        )
        running = cls._execution_output_repo._count_by_status(
            session, execution_id=execution_id, status="RUNNING"
        )
        success = cls._execution_output_repo._count_by_status(
            session, execution_id=execution_id, status="SUCCESS"
        )
        failed = cls._execution_output_repo._count_by_status(
            session, execution_id=execution_id, status="FAILED"
        )
        timeout = cls._execution_output_repo._count_by_status(
            session, execution_id=execution_id, status="TIMEOUT"
        )
        skipped = cls._execution_output_repo._count_by_status(
            session, execution_id=execution_id, status="SKIPPED"
        )
        cancelled = cls._execution_output_repo._count_by_status(
            session, execution_id=execution_id, status="CANCELLED"
        )
        
        return {
            "execution_id": execution_id,
            "total": total,
            "pending": pending,
            "running": running,
            "success": success,
            "failed": failed,
            "timeout": timeout,
            "skipped": skipped,
            "cancelled": cancelled,
            "completed": success + failed + timeout + skipped + cancelled
        }
