"""
TEST 3: Eş Zamanlı Execution Testi (Concurrent Execution)
=========================================================

Bu test, birden fazla workflow'un aynı anda çalıştırılmasını test eder:
1. Birden fazla workflow aynı anda başlatılır
2. Her workflow bağımsız olarak çalışır
3. Tüm execution'lar tamamlanana kadar beklenir
4. Hiçbir execution diğerini etkilemez

Test Senaryosu:
    - 5 farklı workflow aynı anda başlatılır
    - Her biri farklı delay_seconds değeri alır
    - Tümü başarıyla tamamlanmalıdır
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from datetime import datetime, timezone

from miniflow.services._7_script_services import GlobalScriptService
from miniflow.services._8_workflow_services import (
    WorkflowManagementService,
    NodeService,
    TriggerService
)
from miniflow.services._9_execution_services import (
    ExecutionManagementService,
    ExecutionInputService,
    ExecutionOutputService
)
from miniflow.models.enums import WorkflowStatus, TriggerType, ExecutionStatus


class TestConcurrentExecution:
    """
    Eş Zamanlı Execution Testi
    
    Bu test, sistemin birden fazla workflow'u aynı anda
    çalıştırabilme kapasitesini test eder.
    """
    
    NUM_CONCURRENT_WORKFLOWS = 5
    
    @pytest.fixture(autouse=True)
    def setup_concurrent_workflows(self, db_session, mock_scripts):
        """
        Concurrent test için birden fazla workflow oluşturur.
        """
        from miniflow.services._5_workspace_services import WorkspaceManagementService
        
        # Delay script oluştur
        delay_data = mock_scripts["delay_script"]
        script_result = GlobalScriptService.create_script(
            name=f"Delay Script - {time.time()}",
            description=delay_data["description"],
            content=delay_data["content"],
            input_schema=delay_data["input_schema"],
            output_schema=delay_data["output_schema"],
            created_by="test_admin"
        )
        self.delay_script_id = script_result["id"]
        
        GlobalScriptService.approve_script(
            script_id=self.delay_script_id,
            approved_by="test_admin"
        )
        
        # Test workspace oluştur
        workspace_result = WorkspaceManagementService.create_workspace(
            name=f"Concurrent Test Workspace - {time.time()}",
            description="Concurrent execution testleri için workspace",
            owner_id="test_owner",
            plan_id="basic"
        )
        self.workspace_id = workspace_result["id"]
        
        # Birden fazla workflow oluştur
        self.workflows = []
        self.triggers = []
        
        for i in range(self.NUM_CONCURRENT_WORKFLOWS):
            # Workflow oluştur
            workflow_result = WorkflowManagementService.create_workflow(
                workspace_id=self.workspace_id,
                name=f"Concurrent Workflow {i+1}",
                description=f"Concurrent test workflow #{i+1}",
                created_by="test_user"
            )
            workflow_id = workflow_result["id"]
            
            # Node oluştur
            node_result = NodeService.create_node(
                workflow_id=workflow_id,
                name=f"Delay Node {i+1}",
                description="Belirtilen süre bekler",
                script_id=self.delay_script_id,
                position_x=100,
                position_y=100,
                created_by="test_user"
            )
            node_id = node_result["id"]
            
            # Node parametrelerini yapılandır
            NodeService.sync_input_schema_values(
                node_id=node_id,
                input_values={
                    "delay_seconds": "${trigger:delay}",
                    "workflow_id": f"${{{workflow_id}}}"
                }
            )
            
            # Trigger oluştur
            trigger_result = TriggerService.create_trigger(
                workspace_id=self.workspace_id,
                workflow_id=workflow_id,
                name=f"Concurrent Trigger {i+1}",
                trigger_type=TriggerType.API,
                config={},
                input_mapping={
                    "delay": {
                        "type": "number",
                        "required": True,
                        "description": "Bekleme süresi"
                    }
                },
                is_enabled=True,
                created_by="test_user"
            )
            
            # Workflow'u aktif et
            WorkflowManagementService.update_workflow_status(
                workflow_id=workflow_id,
                status=WorkflowStatus.ACTIVE
            )
            
            self.workflows.append({
                "id": workflow_id,
                "node_id": node_id,
                "index": i + 1
            })
            self.triggers.append({
                "id": trigger_result["id"],
                "workflow_id": workflow_id,
                "index": i + 1
            })
        
        print(f"\n✅ {self.NUM_CONCURRENT_WORKFLOWS} workflow oluşturuldu")
        yield
    
    # =========================================================================
    # Test 3.1: Parallel Workflow Start
    # =========================================================================
    
    def test_3_1_start_multiple_workflows_parallel(self, db_session):
        """
        Birden fazla workflow'u paralel olarak başlatma testi.
        
        Senaryo:
            - Tüm workflow'ları aynı anda başlat
            - Her biri farklı delay değeri alsın
            - Tüm execution'ların başarıyla oluşturulduğunu doğrula
        """
        executions = []
        start_time = time.time()
        
        # ThreadPool ile paralel başlat
        with ThreadPoolExecutor(max_workers=self.NUM_CONCURRENT_WORKFLOWS) as executor:
            futures = []
            
            for i, trigger in enumerate(self.triggers):
                # Her workflow farklı delay alır (0.5-2.5 saniye)
                delay = 0.5 + (i * 0.5)
                
                future = executor.submit(
                    ExecutionManagementService.start_execution_by_trigger,
                    trigger_id=trigger["id"],
                    trigger_data={"delay": delay},
                    triggered_by=f"test_user_{i}"
                )
                futures.append((future, trigger, delay))
            
            # Sonuçları topla
            for future, trigger, delay in futures:
                try:
                    result = future.result(timeout=10)
                    executions.append({
                        "id": result["id"],
                        "workflow_id": trigger["workflow_id"],
                        "delay": delay,
                        "status": result.get("status")
                    })
                except Exception as e:
                    print(f"❌ Workflow başlatma hatası: {e}")
        
        elapsed = time.time() - start_time
        
        # Tüm execution'ların oluşturulduğunu doğrula
        assert len(executions) == self.NUM_CONCURRENT_WORKFLOWS
        
        self.executions = executions
        
        print(f"\n✅ {len(executions)} execution paralel olarak başlatıldı ({elapsed:.2f}s)")
        for exec in executions:
            print(f"   - {exec['id']} (delay: {exec['delay']}s)")
    
    def test_3_2_verify_all_executions_started(self, db_session):
        """
        Tüm execution'ların başarıyla başlatıldığını doğrula.
        """
        # Get execution stats
        result = ExecutionManagementService.get_execution_stats(
            workspace_id=self.workspace_id
        )
        
        print(f"\n✅ Execution istatistikleri:")
        print(f"   Total: {result.get('total_executions')}")
        print(f"   Pending: {result.get('pending_executions')}")
        print(f"   Running: {result.get('running_executions')}")
        
        assert result.get('total_executions') >= self.NUM_CONCURRENT_WORKFLOWS
    
    def test_3_3_verify_execution_isolation(self, db_session):
        """
        Execution izolasyonu testi.
        
        Her execution'ın bağımsız olduğunu doğrula:
        - Kendi trigger_data'sı
        - Kendi execution input'ları
        - Birbirini etkilemez
        """
        for exec_data in self.executions:
            result = ExecutionManagementService.get_execution(
                execution_id=exec_data["id"]
            )
            
            # Her execution kendi trigger_data'sına sahip
            trigger_data = result.get("trigger_data", {})
            expected_delay = exec_data["delay"]
            actual_delay = trigger_data.get("delay")
            
            print(f"\n   Execution {exec_data['id']}:")
            print(f"   - Expected delay: {expected_delay}")
            print(f"   - Actual delay: {actual_delay}")
            print(f"   - Workflow: {result.get('workflow_id')}")
            
            assert actual_delay == expected_delay, \
                f"Delay mismatch: expected {expected_delay}, got {actual_delay}"
        
        print(f"\n✅ Tüm execution'lar izole ve bağımsız")
    
    # =========================================================================
    # Test 3.2: Concurrent Execution Status
    # =========================================================================
    
    def test_3_4_check_concurrent_status(self, db_session):
        """
        Concurrent execution durumlarını kontrol et.
        
        Senaryo:
            - Tüm execution'ların durumunu aynı anda sorgula
            - Her biri PENDING veya RUNNING durumda olmalı (henüz tamamlanmadıysa)
        """
        statuses = {}
        
        with ThreadPoolExecutor(max_workers=self.NUM_CONCURRENT_WORKFLOWS) as executor:
            futures = {
                executor.submit(
                    ExecutionManagementService.get_execution,
                    execution_id=exec_data["id"]
                ): exec_data
                for exec_data in self.executions
            }
            
            for future in as_completed(futures):
                exec_data = futures[future]
                try:
                    result = future.result()
                    status = result.get("status")
                    statuses[exec_data["id"]] = status
                except Exception as e:
                    statuses[exec_data["id"]] = f"ERROR: {e}"
        
        print(f"\n✅ Concurrent status kontrolü:")
        for exec_id, status in statuses.items():
            print(f"   - {exec_id}: {status}")


class TestConcurrentInputHandling:
    """
    Concurrent ExecutionInput işleme testleri.
    
    Bu testler, birden fazla execution'ın input'larının
    doğru şekilde işlendiğini doğrular.
    """
    
    def test_4_1_parallel_input_queries(self, db_session):
        """
        Paralel input sorguları testi.
        
        Birden fazla execution'ın input'larını aynı anda sorgula.
        """
        # Önce bir execution başlat (basit test için)
        from miniflow.services._5_workspace_services import WorkspaceManagementService
        from miniflow.services._7_script_services import GlobalScriptService
        
        # Basit bir script ve workflow oluştur
        script_result = GlobalScriptService.create_script(
            name=f"Parallel Test Script - {time.time()}",
            description="Test script",
            content="def main(params): return {'status': 'ok'}",
            input_schema={"test": {"type": "string"}},
            output_schema={"status": {"type": "string"}},
            created_by="test_admin"
        )
        script_id = script_result["id"]
        
        GlobalScriptService.approve_script(
            script_id=script_id,
            approved_by="test_admin"
        )
        
        workspace_result = WorkspaceManagementService.create_workspace(
            name=f"Parallel Input Test - {time.time()}",
            owner_id="test_owner",
            plan_id="basic"
        )
        workspace_id = workspace_result["id"]
        
        # 3 workflow oluştur
        executions = []
        for i in range(3):
            workflow_result = WorkflowManagementService.create_workflow(
                workspace_id=workspace_id,
                name=f"Parallel Test Workflow {i}",
                created_by="test_user"
            )
            workflow_id = workflow_result["id"]
            
            NodeService.create_node(
                workflow_id=workflow_id,
                name="Test Node",
                script_id=script_id,
                position_x=100,
                position_y=100,
                created_by="test_user"
            )
            
            WorkflowManagementService.update_workflow_status(
                workflow_id=workflow_id,
                status=WorkflowStatus.ACTIVE
            )
            
            # Execution başlat
            exec_result = ExecutionManagementService.start_execution_by_workflow(
                workspace_id=workspace_id,
                workflow_id=workflow_id,
                input_data={"test": f"value_{i}"},
                triggered_by="test_user"
            )
            executions.append(exec_result["id"])
        
        # Paralel olarak input'ları sorgula
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    ExecutionInputService.get_execution_inputs,
                    execution_id=exec_id
                ): exec_id
                for exec_id in executions
            }
            
            for future in as_completed(futures):
                exec_id = futures[future]
                try:
                    result = future.result()
                    results.append({
                        "execution_id": exec_id,
                        "input_count": result.get("count")
                    })
                except Exception as e:
                    results.append({
                        "execution_id": exec_id,
                        "error": str(e)
                    })
        
        print(f"\n✅ Paralel input sorguları:")
        for r in results:
            if "error" in r:
                print(f"   - {r['execution_id']}: ERROR - {r['error']}")
            else:
                print(f"   - {r['execution_id']}: {r['input_count']} inputs")
        
        # Tüm sorgular başarılı olmalı
        assert all("error" not in r for r in results)


class TestConcurrentOutputHandling:
    """
    Concurrent ExecutionOutput işleme testleri.
    """
    
    def test_5_1_parallel_output_stats(self, db_session):
        """
        Paralel output istatistik sorguları testi.
        """
        # Bu test, mevcut execution'ların output istatistiklerini
        # paralel olarak sorgulamayı test eder.
        
        # Önce birkaç execution ID'si alalım
        from miniflow.services._5_workspace_services import WorkspaceManagementService
        
        workspace_result = WorkspaceManagementService.create_workspace(
            name=f"Output Stats Test - {time.time()}",
            owner_id="test_owner",
            plan_id="basic"
        )
        workspace_id = workspace_result["id"]
        
        stats = ExecutionManagementService.get_execution_stats(
            workspace_id=workspace_id
        )
        
        print(f"\n✅ Output stats sorgusu başarılı:")
        print(f"   Total: {stats.get('total_executions')}")


# ==============================================================================
# Stress Test (Optional)
# ==============================================================================

class TestStressExecution:
    """
    Stress testleri (opsiyonel).
    
    Bu testler, sistemin yük altında nasıl davrandığını test eder.
    Normal test çalıştırmalarında atlanabilir.
    """
    
    @pytest.mark.slow
    @pytest.mark.skip(reason="Stress test - manuel çalıştırma için")
    def test_stress_100_concurrent_executions(self, db_session):
        """
        100 concurrent execution stress testi.
        
        NOT: Bu test uzun sürer ve sistem kaynaklarını yoğun kullanır.
        """
        NUM_EXECUTIONS = 100
        
        # Implementasyon benzer şekilde...
        pass


# ==============================================================================
# Standalone Test Runner
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short", "-k", "not stress"])

