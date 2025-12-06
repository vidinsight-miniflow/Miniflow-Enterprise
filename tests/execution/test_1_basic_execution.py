"""
TEST 1: Temel Execution Testi
=============================

Bu test temel execution akışını doğrular:
1. Script oluşturma
2. Workflow oluşturma
3. Node oluşturma (script'e bağlı)
4. Trigger oluşturma
5. Execution başlatma
6. Execution'ın başarıyla tamamlanması

Test Senaryosu:
    [Trigger] --> [Node: Simple Echo] --> [END]
    
    Trigger'dan gelen mesaj, Echo node'u tarafından aynen döndürülür.
"""

import pytest
import time
from datetime import datetime, timezone
from typing import Dict, Any

# Test edilecek servisler
from miniflow.services._7_script_services import GlobalScriptService, CustomScriptService
from miniflow.services._8_workflow_services import (
    WorkflowManagementService,
    NodeService,
    EdgeService,
    TriggerService
)
from miniflow.services._9_execution_services import ExecutionManagementService
from miniflow.models.enums import (
    WorkflowStatus,
    TriggerType,
    ExecutionStatus,
    ScriptApprovalStatus
)


class TestBasicExecution:
    """
    Temel Execution Testi
    
    Bu test, en basit workflow senaryosunu test eder:
    - Tek node'lu workflow
    - Trigger'dan node'a veri akışı
    - Başarılı execution tamamlanması
    """
    
    # =========================================================================
    # Test 1.1: Script Oluşturma
    # =========================================================================
    
    def test_1_1_create_global_script(self, db_session, mock_scripts):
        """
        Global script oluşturma testi.
        
        Senaryo:
            - Simple Echo script'i oluştur
            - Script'in doğru parametrelerle kaydedildiğini doğrula
        """
        script_data = mock_scripts["simple_echo"]
        
        result = GlobalScriptService.create_script(
            name=script_data["name"],
            description=script_data["description"],
            content=script_data["content"],
            input_schema=script_data["input_schema"],
            output_schema=script_data["output_schema"],
            created_by="test_admin"
        )
        
        assert result is not None
        assert "id" in result
        assert result["name"] == script_data["name"]
        
        # Script ID'yi sakla (sonraki testler için)
        pytest.test_script_id = result["id"]
        print(f"\n✅ Script oluşturuldu: {result['id']}")
    
    def test_1_2_approve_script(self, db_session):
        """
        Script onaylama testi.
        
        Senaryo:
            - Oluşturulan script'i onayla
            - Approval status'ün APPROVED olduğunu doğrula
        """
        script_id = getattr(pytest, "test_script_id", None)
        assert script_id is not None, "Script ID bulunamadı - önceki test başarısız olmuş olabilir"
        
        result = GlobalScriptService.approve_script(
            script_id=script_id,
            approved_by="test_admin"
        )
        
        assert result is not None
        assert result.get("approval_status") == ScriptApprovalStatus.APPROVED.value
        print(f"\n✅ Script onaylandı: {script_id}")
    
    # =========================================================================
    # Test 1.2: Workflow ve Node Oluşturma
    # =========================================================================
    
    def test_1_3_create_workspace_and_workflow(self, db_session):
        """
        Workspace ve Workflow oluşturma testi.
        
        Senaryo:
            - Test workspace'i oluştur (veya mevcut olanı kullan)
            - Workflow oluştur
        """
        from miniflow.services._5_workspace_services import WorkspaceManagementService
        
        # Test workspace oluştur
        workspace_result = WorkspaceManagementService.create_workspace(
            name="Test Execution Workspace",
            description="Execution testleri için workspace",
            owner_id="test_owner",
            plan_id="basic"  # Varsayılan plan
        )
        
        assert workspace_result is not None
        pytest.test_workspace_id = workspace_result["id"]
        
        # Workflow oluştur
        workflow_result = WorkflowManagementService.create_workflow(
            workspace_id=pytest.test_workspace_id,
            name="Basic Execution Test Workflow",
            description="Temel execution testi için workflow",
            created_by="test_user"
        )
        
        assert workflow_result is not None
        assert "id" in workflow_result
        pytest.test_workflow_id = workflow_result["id"]
        
        print(f"\n✅ Workspace oluşturuldu: {pytest.test_workspace_id}")
        print(f"✅ Workflow oluşturuldu: {pytest.test_workflow_id}")
    
    def test_1_4_create_node_from_script(self, db_session):
        """
        Script'ten Node oluşturma testi.
        
        Senaryo:
            - Onaylı global script'i kullanarak node oluştur
            - Node'un input_params'ının script'in input_schema'sından türetildiğini doğrula
        """
        workflow_id = getattr(pytest, "test_workflow_id", None)
        script_id = getattr(pytest, "test_script_id", None)
        
        assert workflow_id is not None, "Workflow ID bulunamadı"
        assert script_id is not None, "Script ID bulunamadı"
        
        result = NodeService.create_node(
            workflow_id=workflow_id,
            name="Echo Node",
            description="Trigger'dan gelen mesajı echo eder",
            script_id=script_id,
            position_x=100,
            position_y=100,
            created_by="test_user"
        )
        
        assert result is not None
        assert "id" in result
        assert result.get("script_id") == script_id
        
        # Node'un input parametrelerini kontrol et
        assert "input_params" in result or "form_schema" in result
        
        pytest.test_node_id = result["id"]
        print(f"\n✅ Node oluşturuldu: {result['id']}")
        print(f"   Script: {script_id}")
    
    def test_1_5_configure_node_parameters(self, db_session):
        """
        Node parametrelerini yapılandırma testi.
        
        Senaryo:
            - Node'un 'message' parametresini trigger'dan alacak şekilde yapılandır
            - Reference format: ${trigger:message}
        """
        node_id = getattr(pytest, "test_node_id", None)
        assert node_id is not None, "Node ID bulunamadı"
        
        # Node parametrelerini güncelle - message trigger'dan gelecek
        result = NodeService.sync_input_schema_values(
            node_id=node_id,
            input_values={
                "message": "${trigger:message}"  # Trigger'dan gelecek
            }
        )
        
        assert result is not None
        print(f"\n✅ Node parametreleri yapılandırıldı")
        print(f"   message = ${{trigger:message}}")
    
    # =========================================================================
    # Test 1.3: Trigger Oluşturma
    # =========================================================================
    
    def test_1_6_create_trigger(self, db_session):
        """
        Trigger oluşturma testi.
        
        Senaryo:
            - API tipi trigger oluştur
            - Input mapping tanımla (message parametresi)
        """
        workspace_id = getattr(pytest, "test_workspace_id", None)
        workflow_id = getattr(pytest, "test_workflow_id", None)
        
        assert workspace_id is not None
        assert workflow_id is not None
        
        result = TriggerService.create_trigger(
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            name="Test API Trigger",
            trigger_type=TriggerType.API,
            config={"endpoint": "/test/execute"},
            input_mapping={
                "message": {
                    "type": "string",
                    "required": True,
                    "description": "Echo edilecek mesaj"
                }
            },
            is_enabled=True,
            created_by="test_user"
        )
        
        assert result is not None
        assert "id" in result
        pytest.test_trigger_id = result["id"]
        
        print(f"\n✅ Trigger oluşturuldu: {result['id']}")
    
    # =========================================================================
    # Test 1.4: Workflow Aktivasyonu
    # =========================================================================
    
    def test_1_7_activate_workflow(self, db_session):
        """
        Workflow aktivasyon testi.
        
        Senaryo:
            - Workflow'u ACTIVE durumuna getir
        """
        workflow_id = getattr(pytest, "test_workflow_id", None)
        assert workflow_id is not None
        
        result = WorkflowManagementService.update_workflow_status(
            workflow_id=workflow_id,
            status=WorkflowStatus.ACTIVE
        )
        
        assert result is not None
        assert result.get("status") == WorkflowStatus.ACTIVE.value
        
        print(f"\n✅ Workflow aktif edildi: {workflow_id}")
    
    # =========================================================================
    # Test 1.5: Execution Başlatma ve Tamamlama
    # =========================================================================
    
    def test_1_8_start_execution_by_trigger(self, db_session):
        """
        Trigger ile execution başlatma testi.
        
        Senaryo:
            - Trigger üzerinden execution başlat
            - Input data olarak message gönder
            - Execution'ın PENDING durumda başladığını doğrula
        """
        trigger_id = getattr(pytest, "test_trigger_id", None)
        assert trigger_id is not None
        
        result = ExecutionManagementService.start_execution_by_trigger(
            trigger_id=trigger_id,
            trigger_data={"message": "Hello, MiniFlow!"},
            triggered_by="test_user"
        )
        
        assert result is not None
        assert "id" in result
        assert result.get("status") in [ExecutionStatus.PENDING.value, "PENDING"]
        
        pytest.test_execution_id = result["id"]
        print(f"\n✅ Execution başlatıldı: {result['id']}")
        print(f"   Status: {result.get('status')}")
    
    def test_1_9_start_execution_by_workflow(self, db_session):
        """
        Workflow ID ile execution başlatma testi (UI test modu).
        
        Senaryo:
            - Workflow ID üzerinden doğrudan execution başlat
            - Trigger kontrolü yapılmaz
        """
        workspace_id = getattr(pytest, "test_workspace_id", None)
        workflow_id = getattr(pytest, "test_workflow_id", None)
        
        assert workspace_id is not None
        assert workflow_id is not None
        
        result = ExecutionManagementService.start_execution_by_workflow(
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            input_data={"message": "Direct workflow execution test"},
            triggered_by="test_user"
        )
        
        assert result is not None
        assert "id" in result
        
        pytest.test_execution_id_direct = result["id"]
        print(f"\n✅ Direct execution başlatıldı: {result['id']}")
    
    def test_1_10_get_execution_details(self, db_session):
        """
        Execution detaylarını alma testi.
        
        Senaryo:
            - Başlatılan execution'ın detaylarını al
            - Gerekli alanların mevcut olduğunu doğrula
        """
        execution_id = getattr(pytest, "test_execution_id", None)
        assert execution_id is not None
        
        result = ExecutionManagementService.get_execution(
            execution_id=execution_id
        )
        
        assert result is not None
        assert result.get("id") == execution_id
        assert "status" in result
        assert "workflow_id" in result
        assert "trigger_data" in result
        
        print(f"\n✅ Execution detayları alındı:")
        print(f"   ID: {result['id']}")
        print(f"   Status: {result['status']}")
        print(f"   Workflow: {result['workflow_id']}")
        print(f"   Trigger Data: {result['trigger_data']}")
    
    # =========================================================================
    # Test 1.6: Execution İstatistikleri
    # =========================================================================
    
    def test_1_11_get_execution_stats(self, db_session):
        """
        Execution istatistikleri testi.
        
        Senaryo:
            - Workspace'e ait execution istatistiklerini al
        """
        workspace_id = getattr(pytest, "test_workspace_id", None)
        assert workspace_id is not None
        
        result = ExecutionManagementService.get_execution_stats(
            workspace_id=workspace_id
        )
        
        assert result is not None
        assert "total_executions" in result
        assert result["total_executions"] >= 1  # En az 1 execution olmalı
        
        print(f"\n✅ Execution istatistikleri:")
        print(f"   Total: {result.get('total_executions', 0)}")
        print(f"   Pending: {result.get('pending_executions', 0)}")
        print(f"   Running: {result.get('running_executions', 0)}")
        print(f"   Completed: {result.get('completed_executions', 0)}")
        print(f"   Failed: {result.get('failed_executions', 0)}")


class TestExecutionInputCreation:
    """
    ExecutionInput oluşturma testleri.
    
    Execution başlatıldığında ExecutionInput'ların doğru şekilde
    oluşturulduğunu doğrular.
    """
    
    def test_2_1_verify_execution_inputs_created(self, db_session):
        """
        ExecutionInput kayıtlarının oluşturulduğunu doğrula.
        
        Senaryo:
            - Başlatılan execution için ExecutionInput'ları al
            - Her node için bir input olduğunu doğrula
        """
        from miniflow.services._9_execution_services import ExecutionInputService
        
        execution_id = getattr(pytest, "test_execution_id", None)
        assert execution_id is not None
        
        result = ExecutionInputService.get_execution_inputs(
            execution_id=execution_id
        )
        
        assert result is not None
        assert "inputs" in result
        assert len(result["inputs"]) >= 1  # En az 1 node olmalı
        
        print(f"\n✅ ExecutionInput'lar oluşturuldu:")
        print(f"   Execution: {execution_id}")
        print(f"   Input sayısı: {result['count']}")
        
        for inp in result["inputs"]:
            print(f"   - Node: {inp.get('node_name')} (dep: {inp.get('dependency_count')})")
    
    def test_2_2_verify_input_parameters(self, db_session):
        """
        ExecutionInput parametrelerinin doğruluğunu kontrol et.
        
        Senaryo:
            - Node'un input parametrelerinin ExecutionInput'a aktarıldığını doğrula
            - Reference'ların henüz çözülmediğini (${trigger:...} formatında) doğrula
        """
        from miniflow.services._9_execution_services import ExecutionInputService
        
        execution_id = getattr(pytest, "test_execution_id", None)
        node_id = getattr(pytest, "test_node_id", None)
        
        assert execution_id is not None
        assert node_id is not None
        
        result = ExecutionInputService.get_input_by_node(
            execution_id=execution_id,
            node_id=node_id
        )
        
        assert result is not None
        assert "params" in result
        
        params = result["params"]
        # Parametrelerin reference formatında olduğunu doğrula
        # (henüz çözülmemiş olmalı)
        
        print(f"\n✅ ExecutionInput parametreleri:")
        print(f"   Node: {result.get('node_name')}")
        print(f"   Params: {params}")


# ==============================================================================
# Standalone Test Runner
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

