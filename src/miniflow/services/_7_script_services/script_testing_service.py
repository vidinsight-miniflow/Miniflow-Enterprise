from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import ScriptTestStatus
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class ScriptTestingService:
    """
    Script test yönetim servisi.
    
    Custom script'lerin test durumlarını ve sonuçlarını yönetir.
    NOT: Gerçek test execution'ı ayrı bir worker/executor tarafından yapılır.
    Bu servis sadece test durumlarını günceller.
    """
    _registry = RepositoryRegistry()
    _custom_script_repo = _registry.custom_script_repository()

    # ==================================================================================== UPDATE TEST STATUS ==
    @classmethod
    @with_transaction(manager=None)
    def mark_test_passed(
        cls,
        session,
        *,
        script_id: str,
        test_results: Optional[Dict[str, Any]] = None,
        test_coverage: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Script testinin başarılı olduğunu işaretler.
        
        Args:
            script_id: Script ID'si
            test_results: Test sonuçları (opsiyonel)
            test_coverage: Test coverage yüzdesi (opsiyonel)
            
        Returns:
            {"success": True, "test_status": "PASSED"}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._update_test_status(
            session,
            script_id=script_id,
            test_status=ScriptTestStatus.PASSED,
            test_results=test_results,
            test_coverage=test_coverage
        )
        
        return {
            "success": True,
            "test_status": "PASSED",
            "test_coverage": test_coverage
        }

    @classmethod
    @with_transaction(manager=None)
    def mark_test_failed(
        cls,
        session,
        *,
        script_id: str,
        test_results: Dict[str, Any],
        test_coverage: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Script testinin başarısız olduğunu işaretler.
        
        Args:
            script_id: Script ID'si
            test_results: Test sonuçları (hata detayları, zorunlu)
            test_coverage: Test coverage yüzdesi (opsiyonel)
            
        Returns:
            {"success": True, "test_status": "FAILED"}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._update_test_status(
            session,
            script_id=script_id,
            test_status=ScriptTestStatus.FAILED,
            test_results=test_results,
            test_coverage=test_coverage
        )
        
        return {
            "success": True,
            "test_status": "FAILED"
        }

    @classmethod
    @with_transaction(manager=None)
    def mark_test_skipped(
        cls,
        session,
        *,
        script_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Script testinin atlandığını işaretler.
        
        Args:
            script_id: Script ID'si
            reason: Atlama nedeni (opsiyonel)
            
        Returns:
            {"success": True, "test_status": "SKIPPED"}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        test_results = {"skipped_reason": reason} if reason else {}
        
        cls._custom_script_repo._update_test_status(
            session,
            script_id=script_id,
            test_status=ScriptTestStatus.SKIPPED,
            test_results=test_results
        )
        
        return {
            "success": True,
            "test_status": "SKIPPED",
            "reason": reason
        }

    @classmethod
    @with_transaction(manager=None)
    def reset_test_status(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script test durumunu UNTESTED'e sıfırlar.
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"success": True, "test_status": "UNTESTED"}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._update_test_status(
            session,
            script_id=script_id,
            test_status=ScriptTestStatus.UNTESTED,
            test_results={},
            test_coverage=None
        )
        
        return {
            "success": True,
            "test_status": "UNTESTED"
        }

    # ==================================================================================== READ TEST INFO ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_test_status(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script test durumunu getirir.
        
        Args:
            script_id: Script ID'si
            
        Returns:
            Test durumu ve sonuçları
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        return {
            "script_id": script.id,
            "script_name": script.name,
            "test_status": script.test_status.value if script.test_status else None,
            "test_coverage": script.test_coverage,
            "test_results": script.test_results,
            "is_dangerous": script.is_dangerous
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_untested_scripts(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Test edilmemiş script'leri listeler.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {"workspace_id": str, "scripts": List[Dict], "count": int}
        """
        scripts = cls._custom_script_repo._get_all_by_workspace_id(
            session, 
            workspace_id=workspace_id
        )
        
        untested = [s for s in scripts if s.test_status == ScriptTestStatus.UNTESTED]
        
        return {
            "workspace_id": workspace_id,
            "scripts": [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category,
                    "approval_status": s.approval_status.value if s.approval_status else None,
                    "is_dangerous": s.is_dangerous,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in untested
            ],
            "count": len(untested)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_failed_scripts(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Testi başarısız olan script'leri listeler.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {"workspace_id": str, "scripts": List[Dict], "count": int}
        """
        scripts = cls._custom_script_repo._get_all_by_workspace_id(
            session, 
            workspace_id=workspace_id
        )
        
        failed = [s for s in scripts if s.test_status == ScriptTestStatus.FAILED]
        
        return {
            "workspace_id": workspace_id,
            "scripts": [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category,
                    "test_results": s.test_results,
                    "is_dangerous": s.is_dangerous,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in failed
            ],
            "count": len(failed)
        }

    # ==================================================================================== BULK UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_test_results(
        cls,
        session,
        *,
        script_id: str,
        test_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Test sonuçlarını günceller (durum değiştirmeden).
        
        Args:
            script_id: Script ID'si
            test_results: Test sonuçları
            
        Returns:
            {"success": True}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._update(
            session,
            record_id=script_id,
            test_results=test_results
        )
        
        return {"success": True}

    @classmethod
    @with_transaction(manager=None)
    def update_test_coverage(
        cls,
        session,
        *,
        script_id: str,
        test_coverage: float,
    ) -> Dict[str, Any]:
        """
        Test coverage'ı günceller.
        
        Args:
            script_id: Script ID'si
            test_coverage: Coverage yüzdesi (0-100)
            
        Returns:
            {"success": True, "test_coverage": float}
        """
        if test_coverage < 0 or test_coverage > 100:
            raise BusinessRuleViolationError(
                rule_name="invalid_coverage",
                message="Test coverage must be between 0 and 100"
            )
        
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._update(
            session,
            record_id=script_id,
            test_coverage=test_coverage
        )
        
        return {
            "success": True,
            "test_coverage": test_coverage
        }

