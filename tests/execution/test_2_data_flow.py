"""
TEST 2: Değişken Aktarım Testi (Data Flow)
==========================================

Bu test, node'lar arası veri akışını doğrular:
1. Trigger'dan ilk node'a veri aktarımı
2. Node'dan node'a veri aktarımı
3. Zincirleme değişken referansları

Test Senaryosu:
    [Trigger] --> [Node 1: Transform] --> [Node 2: Transform] --> [Node 3: Accumulate] --> [END]
    
    - Trigger: {"initial_value": "START"}
    - Node 1: input_value = ${trigger:initial_value} --> output: "processed_START"
    - Node 2: input_value = ${node:NODE1.output_value} --> output: "processed_processed_START"
    - Node 3: values = [${node:NODE1.output_value}, ${node:NODE2.output_value}] --> combined result
"""

import pytest
import time
from typing import Dict, Any, List

from miniflow.services._7_script_services import GlobalScriptService
from miniflow.services._8_workflow_services import (
    WorkflowManagementService,
    NodeService,
    EdgeService,
    TriggerService
)
from miniflow.services._9_execution_services import (
    ExecutionManagementService,
    ExecutionInputService,
    ExecutionOutputService
)
from miniflow.models.enums import WorkflowStatus, TriggerType, ExecutionStatus


class TestDataFlowExecution:
    """
    Veri Akışı Execution Testi
    
    Bu test, birden fazla node arasında veri akışını test eder.
    Her node önceki node'un çıktısını kullanır.
    """
    
    # =========================================================================
    # Setup: Script'leri ve Workflow'u Oluştur
    # =========================================================================
    
    @pytest.fixture(autouse=True)
    def setup_workflow(self, db_session, mock_scripts):
        """Test için gerekli workflow yapısını oluşturur."""
        
        # 1. Transformer Script Oluştur
        transformer_data = mock_scripts["data_transformer"]
        transformer_result = GlobalScriptService.create_script(
            name=f"Data Transformer - {time.time()}",
            description=transformer_data["description"],
            content=transformer_data["content"],
            input_schema=transformer_data["input_schema"],
            output_schema=transformer_data["output_schema"],
            created_by="test_admin"
        )
        self.transformer_script_id = transformer_result["id"]
        
        # Onayla
        GlobalScriptService.approve_script(
            script_id=self.transformer_script_id,
            approved_by="test_admin"
        )
        
        # 2. Accumulator Script Oluştur
        accumulator_data = mock_scripts["accumulator"]
        accumulator_result = GlobalScriptService.create_script(
            name=f"Accumulator - {time.time()}",
            description=accumulator_data["description"],
            content=accumulator_data["content"],
            input_schema=accumulator_data["input_schema"],
            output_schema=accumulator_data["output_schema"],
            created_by="test_admin"
        )
        self.accumulator_script_id = accumulator_result["id"]
        
        GlobalScriptService.approve_script(
            script_id=self.accumulator_script_id,
            approved_by="test_admin"
        )
        
        # 3. Workspace Oluştur
        from miniflow.services._5_workspace_services import WorkspaceManagementService
        workspace_result = WorkspaceManagementService.create_workspace(
            name=f"Data Flow Test Workspace - {time.time()}",
            description="Data flow testleri için workspace",
            owner_id="test_owner",
            plan_id="basic"
        )
        self.workspace_id = workspace_result["id"]
        
        # 4. Workflow Oluştur
        workflow_result = WorkflowManagementService.create_workflow(
            workspace_id=self.workspace_id,
            name="Data Flow Test Workflow",
            description="Node'lar arası veri akışı testi",
            created_by="test_user"
        )
        self.workflow_id = workflow_result["id"]
        
        yield
        
        # Cleanup gerekirse burada yapılabilir
    
    # =========================================================================
    # Test 2.1: Multi-Node Workflow Oluşturma
    # =========================================================================
    
    def test_2_1_create_chained_nodes(self, db_session):
        """
        Zincirleme node'lar oluşturma testi.
        
        Senaryo:
            - 3 node oluştur: Transform1, Transform2, Accumulator
            - Her node önceki node'a bağlı olacak şekilde edge'ler oluştur
        """
        # Node 1: İlk Transformer
        node1_result = NodeService.create_node(
            workflow_id=self.workflow_id,
            name="Transform Node 1",
            description="Trigger'dan gelen veriyi dönüştürür",
            script_id=self.transformer_script_id,
            position_x=100,
            position_y=200,
            created_by="test_user"
        )
        self.node1_id = node1_result["id"]
        
        # Node 2: İkinci Transformer
        node2_result = NodeService.create_node(
            workflow_id=self.workflow_id,
            name="Transform Node 2",
            description="Node 1'in çıktısını dönüştürür",
            script_id=self.transformer_script_id,
            position_x=300,
            position_y=200,
            created_by="test_user"
        )
        self.node2_id = node2_result["id"]
        
        # Node 3: Accumulator
        node3_result = NodeService.create_node(
            workflow_id=self.workflow_id,
            name="Accumulator Node",
            description="Tüm çıktıları birleştirir",
            script_id=self.accumulator_script_id,
            position_x=500,
            position_y=200,
            created_by="test_user"
        )
        self.node3_id = node3_result["id"]
        
        print(f"\n✅ 3 Node oluşturuldu:")
        print(f"   Node 1 (Transform): {self.node1_id}")
        print(f"   Node 2 (Transform): {self.node2_id}")
        print(f"   Node 3 (Accumulator): {self.node3_id}")
        
        # Edge'leri oluştur: Node1 -> Node2 -> Node3
        edge1_result = EdgeService.create_edge(
            workflow_id=self.workflow_id,
            from_node_id=self.node1_id,
            to_node_id=self.node2_id,
            created_by="test_user"
        )
        
        edge2_result = EdgeService.create_edge(
            workflow_id=self.workflow_id,
            from_node_id=self.node2_id,
            to_node_id=self.node3_id,
            created_by="test_user"
        )
        
        print(f"\n✅ Edge'ler oluşturuldu:")
        print(f"   Node1 -> Node2: {edge1_result['id']}")
        print(f"   Node2 -> Node3: {edge2_result['id']}")
    
    def test_2_2_configure_node_references(self, db_session):
        """
        Node parametrelerini reference'larla yapılandırma testi.
        
        Senaryo:
            - Node 1: input_value = ${trigger:initial_value}
            - Node 2: input_value = ${node:NODE1_ID.output_value}
            - Node 3: values = [${node:NODE1_ID.output_value}, ${node:NODE2_ID.output_value}]
        """
        # Node 1: Trigger'dan değer al
        NodeService.sync_input_schema_values(
            node_id=self.node1_id,
            input_values={
                "input_value": "${trigger:initial_value}",
                "prefix": "step1_"
            }
        )
        
        # Node 2: Node 1'in çıktısını al
        NodeService.sync_input_schema_values(
            node_id=self.node2_id,
            input_values={
                "input_value": f"${{node:{self.node1_id}.output_value}}",
                "prefix": "step2_"
            }
        )
        
        # Node 3: Her iki node'un çıktısını al
        # NOT: Array formatında reference'lar için özel handling gerekebilir
        # Şimdilik basit bir format kullanıyoruz
        NodeService.sync_input_schema_values(
            node_id=self.node3_id,
            input_values={
                "values": f"[${{node:{self.node1_id}.output_value}}, ${{node:{self.node2_id}.output_value}}]",
                "separator": " | "
            }
        )
        
        print(f"\n✅ Node parametreleri yapılandırıldı:")
        print(f"   Node 1: input_value = ${{trigger:initial_value}}")
        print(f"   Node 2: input_value = ${{node:{self.node1_id}.output_value}}")
        print(f"   Node 3: values = [Node1.output, Node2.output]")
    
    def test_2_3_create_trigger_with_input_mapping(self, db_session):
        """
        Input mapping'li trigger oluşturma testi.
        """
        result = TriggerService.create_trigger(
            workspace_id=self.workspace_id,
            workflow_id=self.workflow_id,
            name="Data Flow Trigger",
            trigger_type=TriggerType.API,
            config={},
            input_mapping={
                "initial_value": {
                    "type": "string",
                    "required": True,
                    "description": "Başlangıç değeri"
                },
                "timestamp": {
                    "type": "string",
                    "required": False,
                    "description": "Zaman damgası"
                }
            },
            is_enabled=True,
            created_by="test_user"
        )
        
        self.trigger_id = result["id"]
        print(f"\n✅ Trigger oluşturuldu: {self.trigger_id}")
    
    def test_2_4_activate_workflow(self, db_session):
        """Workflow'u aktif et."""
        result = WorkflowManagementService.update_workflow_status(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.ACTIVE
        )
        
        assert result.get("status") == WorkflowStatus.ACTIVE.value
        print(f"\n✅ Workflow aktif edildi")
    
    # =========================================================================
    # Test 2.2: Execution Başlatma ve Veri Akışı Doğrulama
    # =========================================================================
    
    def test_2_5_start_data_flow_execution(self, db_session):
        """
        Data flow execution başlatma testi.
        
        Senaryo:
            - Trigger ile execution başlat
            - Initial value olarak "HELLO" gönder
            
        Beklenen Akış:
            1. Trigger data: {"initial_value": "HELLO"}
            2. Node 1 output: {"output_value": "step1_HELLO"}
            3. Node 2 output: {"output_value": "step2_step1_HELLO"}
            4. Node 3 output: {"combined_result": "step1_HELLO | step2_step1_HELLO"}
        """
        result = ExecutionManagementService.start_execution_by_trigger(
            trigger_id=self.trigger_id,
            trigger_data={
                "initial_value": "HELLO",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            triggered_by="test_user"
        )
        
        assert result is not None
        self.execution_id = result["id"]
        
        print(f"\n✅ Data Flow Execution başlatıldı: {self.execution_id}")
        print(f"   Trigger data: initial_value=HELLO")
    
    def test_2_6_verify_execution_inputs_dependencies(self, db_session):
        """
        ExecutionInput'ların dependency_count'larını doğrula.
        
        Beklenen:
            - Node 1: dependency_count = 0 (başlangıç node'u)
            - Node 2: dependency_count = 1 (Node 1'e bağlı)
            - Node 3: dependency_count = 1 (Node 2'ye bağlı)
        """
        result = ExecutionInputService.get_execution_inputs(
            execution_id=self.execution_id
        )
        
        inputs_by_node = {inp["node_id"]: inp for inp in result["inputs"]}
        
        # Dependency'leri kontrol et
        node1_input = inputs_by_node.get(self.node1_id)
        node2_input = inputs_by_node.get(self.node2_id)
        node3_input = inputs_by_node.get(self.node3_id)
        
        print(f"\n✅ Dependency kontrolü:")
        
        if node1_input:
            print(f"   Node 1 dependency: {node1_input['dependency_count']} (beklenen: 0)")
            assert node1_input["dependency_count"] == 0
        
        if node2_input:
            print(f"   Node 2 dependency: {node2_input['dependency_count']} (beklenen: 1)")
            assert node2_input["dependency_count"] == 1
        
        if node3_input:
            print(f"   Node 3 dependency: {node3_input['dependency_count']} (beklenen: 1)")
            assert node3_input["dependency_count"] == 1
    
    def test_2_7_verify_pending_and_ready_counts(self, db_session):
        """
        Pending ve ready input sayılarını doğrula.
        """
        result = ExecutionInputService.get_pending_inputs_count(
            execution_id=self.execution_id
        )
        
        print(f"\n✅ Input durumları:")
        print(f"   Ready (dependency=0): {result.get('ready_count')}")
        print(f"   Pending (dependency>0): {result.get('pending_count')}")
        print(f"   Total: {result.get('total')}")
        
        # Başlangıçta sadece Node 1 ready olmalı
        assert result.get("ready_count") >= 1


class TestReferenceResolution:
    """
    Reference çözümleme testleri.
    
    Bu testler, farklı reference tiplerinin doğru çözümlendiğini doğrular.
    """
    
    def test_3_1_static_reference_resolution(self, db_session):
        """
        Static reference çözümleme testi.
        
        Format: ${static:değer}
        """
        from miniflow.services._0_internal_services.scheduler_service import (
            RefrenceResolver,
            SchedulerForInputHandler
        )
        
        # Static reference parse
        ref_info = SchedulerForInputHandler._parse_refrence(
            "${static:test_value}",
            "test_param",
            "string"
        )
        
        assert ref_info["type"] == "static"
        assert ref_info["id_or_value"] == "test_value"
        
        # Değeri çöz
        value = RefrenceResolver.get_static_data(ref_info)
        assert value == "test_value"
        
        print(f"\n✅ Static reference çözümlendi: 'test_value'")
    
    def test_3_2_trigger_reference_format(self, db_session):
        """
        Trigger reference format testi.
        
        Format: ${trigger:path.to.value}
        """
        from miniflow.services._0_internal_services.scheduler_service import (
            SchedulerForInputHandler
        )
        
        # Trigger reference parse
        ref_info = SchedulerForInputHandler._parse_refrence(
            "${trigger:data.user.name}",
            "user_name",
            "string"
        )
        
        assert ref_info["type"] == "trigger"
        assert ref_info["value_path"] == "data.user.name"
        
        print(f"\n✅ Trigger reference parse edildi: path='data.user.name'")
    
    def test_3_3_node_reference_format(self, db_session):
        """
        Node reference format testi.
        
        Format: ${node:NODE_ID.result.data}
        """
        from miniflow.services._0_internal_services.scheduler_service import (
            SchedulerForInputHandler
        )
        
        # Node reference parse
        ref_info = SchedulerForInputHandler._parse_refrence(
            "${node:NOD-12345.result.output}",
            "prev_output",
            "string"
        )
        
        assert ref_info["type"] == "node"
        assert ref_info["id"] == "NOD-12345"
        assert ref_info["value_path"] == "result.output"
        
        print(f"\n✅ Node reference parse edildi: id='NOD-12345', path='result.output'")
    
    def test_3_4_nested_path_resolution(self, db_session):
        """
        İç içe path çözümleme testi.
        
        Test: "data.items[0].name" -> ["data", "items", "[0]", "name"]
        """
        from miniflow.services._0_internal_services.scheduler_service import (
            RefrenceResolver
        )
        
        # Test data
        context = {
            "data": {
                "items": [
                    {"name": "first_item"},
                    {"name": "second_item"}
                ],
                "count": 2
            }
        }
        
        # Path'i parçalara ayır
        path_parts = RefrenceResolver._resolve_nested_reference("data.items[0].name")
        assert path_parts == ["data", "items", "[0]", "name"]
        
        # Değeri çıkar
        value = RefrenceResolver._get_value_from_context(path_parts, context)
        assert value == "first_item"
        
        print(f"\n✅ Nested path çözümlendi: 'data.items[0].name' -> 'first_item'")
    
    def test_3_5_type_conversion(self, db_session):
        """
        Tip dönüşüm testleri.
        """
        from miniflow.services._0_internal_services.scheduler_service import TypeConverter
        
        # String -> Integer
        result = TypeConverter.to_integer("test", "42")
        assert result == 42
        assert isinstance(result, int)
        
        # String -> Float
        result = TypeConverter.to_float("test", "3.14")
        assert result == 3.14
        assert isinstance(result, float)
        
        # String -> Boolean
        result = TypeConverter.to_boolean("test", "true")
        assert result == True
        
        result = TypeConverter.to_boolean("test", "0")
        assert result == False
        
        # JSON String -> Array
        result = TypeConverter.to_array("test", '["a", "b", "c"]')
        assert result == ["a", "b", "c"]
        
        # JSON String -> Object
        result = TypeConverter.to_object("test", '{"key": "value"}')
        assert result == {"key": "value"}
        
        print(f"\n✅ Tüm tip dönüşümleri başarılı")


# ==============================================================================
# Standalone Test Runner
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

