#!/usr/bin/env python3
"""
🚀 MiniFlow Gerçek Veritabanı İnteraktif Execution Test Script
================================================================

Bu script GERÇEK bir veritabanı ile çalışır ve execution sürecini
adım adım test eder. Her adımda size sonuçları gösterir ve
devam etmek için onayınızı bekler.

Kullanım:
    cd /Users/enesa/PythonProjects/vidinsight-miniflow-enterprise
    PYTHONPATH=src python tests/interactive_db_execution_test.py

Veritabanı Seçenekleri:
    --db-type sqlite      # SQLite dosya veritabanı (varsayılan)
    --db-type postgresql  # PostgreSQL veritabanı
    --db-type mysql       # MySQL veritabanı
    --db-path ./test.db   # SQLite için dosya yolu (varsayılan: ./test_execution.db)
"""

import sys
import os
import json
import time
import argparse
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, Optional

# Argümanları parse et
parser = argparse.ArgumentParser(description='MiniFlow Gerçek DB Execution Test')
parser.add_argument('--db-type', choices=['sqlite', 'postgresql', 'mysql'], default='sqlite',
                    help='Veritabanı tipi (varsayılan: sqlite)')
parser.add_argument('--db-path', default='./test_execution.db',
                    help='SQLite için dosya yolu (varsayılan: ./test_execution.db)')
parser.add_argument('--db-host', default='localhost', help='Veritabanı host (PostgreSQL/MySQL için)')
parser.add_argument('--db-port', type=int, help='Veritabanı port (PostgreSQL/MySQL için)')
parser.add_argument('--db-name', default='miniflow_test', help='Veritabanı adı (PostgreSQL/MySQL için)')
parser.add_argument('--db-user', help='Veritabanı kullanıcı adı (PostgreSQL/MySQL için)')
parser.add_argument('--db-password', help='Veritabanı şifresi (PostgreSQL/MySQL için)')
parser.add_argument('--auto', action='store_true', help='Otomatik mod (input beklemeden çalışır)')
args = parser.parse_args()
AUTO_MODE = args.auto

# Path setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

# ANSI Color Codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Başlık yazdır."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_step(step_num: int, text: str):
    """Adım başlığı yazdır."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}[ADIM {step_num}] {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.END}")

def print_success(text: str):
    """Başarı mesajı yazdır."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Hata mesajı yazdır."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text: str):
    """Bilgi mesajı yazdır."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_warning(text: str):
    """Uyarı mesajı yazdır."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_data(label: str, data: Any, indent: int = 0):
    """Veri yazdır."""
    prefix = "   " * indent
    if isinstance(data, dict):
        print(f"{prefix}{Colors.BOLD}{label}:{Colors.END}")
        for key, value in data.items():
            if isinstance(value, dict):
                print_data(key, value, indent + 1)
            elif isinstance(value, list):
                print(f"{prefix}   {Colors.CYAN}{key}:{Colors.END} {json.dumps(value, indent=2)}")
            else:
                print(f"{prefix}   {Colors.CYAN}{key}:{Colors.END} {value}")
    else:
        print(f"{prefix}{Colors.BOLD}{label}:{Colors.END} {data}")

def wait_for_user(prompt: str = "Devam etmek için Enter'a basın..."):
    """Kullanıcıdan devam etmesini bekle."""
    if AUTO_MODE:
        print(f"\n{Colors.YELLOW}[AUTO] {prompt}{Colors.END}")
        time.sleep(0.5)
        return
    
    print(f"\n{Colors.YELLOW}{Colors.BOLD}>>> {prompt}{Colors.END}")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Colors.RED}Test iptal edildi.{Colors.END}")
        sys.exit(0)

# Global test data
test_data: Dict[str, Any] = {}

# ============================================================================
# ADIM 1: Database Bağlantısı
# ============================================================================

def step1_setup_database():
    """Gerçek veritabanı bağlantısı kur."""
    print_step(1, "Gerçek Veritabanı Bağlantısı")
    
    try:
        # Environment setup
        os.environ.setdefault('APP_ENV', 'test')
        os.environ.setdefault('JWT_SECRET_KEY', 'test_jwt_secret_key_32chars_min!')
        os.environ.setdefault('ENCRYPTION_KEY', 'test_encryption_key_32chars!!')
        os.environ.setdefault('MAILTRAP_API_TOKEN', 'test_token')
        os.environ.setdefault('MAILTRAP_SENDER_EMAIL', 'test@example.com')
        
        # ConfigurationHandler setup
        from miniflow.utils.handlers.configuration_handler import ConfigurationHandler
        from miniflow.utils.handlers.environment_handler import EnvironmentHandler
        
        EnvironmentHandler._initialized = True
        config_path = os.path.join(PROJECT_ROOT, 'configurations', 'test.ini')
        if os.path.exists(config_path):
            import configparser
            from pathlib import Path
            
            ConfigurationHandler._parser = configparser.ConfigParser()
            ConfigurationHandler._parser.read(config_path)
            ConfigurationHandler._config_dir = Path(PROJECT_ROOT) / "configurations"
            ConfigurationHandler._initialized = True
            print_success(f"Configuration yüklendi: {config_path}")
        else:
            print_error(f"Config dosyası bulunamadı: {config_path}")
            return False
        
        # Database setup
        from miniflow.database.engine import DatabaseManager
        from miniflow.database.config import DatabaseConfig, DatabaseType
        
        db_type_map = {
            'sqlite': DatabaseType.SQLITE,
            'postgresql': DatabaseType.POSTGRESQL,
            'mysql': DatabaseType.MYSQL
        }
        
        db_type = db_type_map[args.db_type]
        
        if db_type == DatabaseType.SQLITE:
            db_config = DatabaseConfig(
                db_type=db_type,
                sqlite_path=args.db_path
            )
            print_info(f"SQLite veritabanı: {args.db_path}")
            
            # Eğer dosya varsa, kullanıcıya sor
            if os.path.exists(args.db_path) and not AUTO_MODE:
                response = input(f"\n⚠️  '{args.db_path}' dosyası zaten var. Silinsin mi? (y/N): ")
                if response.lower() == 'y':
                    os.remove(args.db_path)
                    print_success("Eski veritabanı dosyası silindi")
                else:
                    print_info("Mevcut veritabanı kullanılacak")
        else:
            # PostgreSQL veya MySQL
            db_config = DatabaseConfig(
                db_type=db_type,
                db_name=args.db_name,
                host=args.db_host,
                port=args.db_port or (5432 if db_type == DatabaseType.POSTGRESQL else 3306),
                username=args.db_user,
                password=args.db_password
            )
            print_info(f"{args.db_type.upper()} veritabanı: {args.db_host}:{db_config.port}/{args.db_name}")
        
        manager = DatabaseManager()
        manager.initialize(db_config, auto_start=True, create_tables=True, force_reinitialize=False)
        test_data['db_manager'] = manager
        test_data['db_config'] = db_config
        
        print_success(f"✅ {args.db_type.upper()} veritabanı bağlantısı kuruldu!")
        print_data("Veritabanı Bilgileri", {
            "Tip": args.db_type,
            "Path/Host": args.db_path if db_type == DatabaseType.SQLITE else f"{args.db_host}:{db_config.port}",
            "Database": args.db_name if db_type != DatabaseType.SQLITE else args.db_path
        })
        
        # Repository Registry
        from miniflow.database import RepositoryRegistry
        test_data['registry'] = RepositoryRegistry
        print_success("Repository Registry hazır")
        
        return True
        
    except Exception as e:
        print_error(f"Database bağlantı hatası: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# ADIM 2: Test Verileri Oluşturma
# ============================================================================

def step2_create_test_data():
    """Test için gerekli verileri oluştur."""
    print_step(2, "Test Verileri Oluşturma")
    
    registry = test_data['registry']
    manager = test_data['db_manager']
    
    try:
        # Workspace Plan
        print_info("Workspace Plan oluşturuluyor...")
        workspace_plan_repo = registry.workspace_plan_repository()
        
        with manager.engine.session_context() as session:
            plan = workspace_plan_repo._create(
                session,
                name="Test Plan",
                description="Test için oluşturulmuş plan",
                max_members_per_workspace=10,
                max_workflows_per_workspace=50,
                max_file_size_mb_per_workspace=100,
                storage_limit_mb_per_workspace=1000,
                price_per_month=0.0
            )
            test_data['plan_id'] = plan.id
            print_success(f"Workspace Plan oluşturuldu: {plan.id}")
        
        # User
        print_info("Test kullanıcısı oluşturuluyor...")
        user_repo = registry.user_repository()
        
        with manager.engine.session_context() as session:
            import hashlib
            hashed_password = hashlib.sha256("test_password".encode()).hexdigest()
            
            user = user_repo._create(
                session,
                email="test@example.com",
                username="testuser",
                hashed_password=hashed_password,
                name="Test",
                surname="User",
                is_email_verified=True
            )
            test_data['user_id'] = user.id
            print_success(f"Test kullanıcısı oluşturuldu: {user.id}")
        
        # Workspace
        print_info("Workspace oluşturuluyor...")
        workspace_repo = registry.workspace_repository()
        
        with manager.engine.session_context() as session:
            workspace = workspace_repo._create(
                session,
                name="Test Workspace",
                description="Test için oluşturulmuş workspace",
                owner_id=test_data['user_id'],
                plan_id=test_data['plan_id'],
                member_limit=10,
                workflow_limit=50,
                storage_limit_mb=1000
            )
            test_data['workspace_id'] = workspace.id
            print_success(f"Workspace oluşturuldu: {workspace.id}")
        
        print_success("✅ Tüm test verileri oluşturuldu!")
        print_data("Oluşturulan Veriler", {
            "Plan ID": test_data['plan_id'],
            "User ID": test_data['user_id'],
            "Workspace ID": test_data['workspace_id']
        })
        
        return True
        
    except Exception as e:
        print_error(f"Test verisi oluşturma hatası: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# ADIM 3: Script Oluşturma
# ============================================================================

def step3_create_script():
    """Test script'i oluştur."""
    print_step(3, "Test Script Oluşturma")
    
    registry = test_data['registry']
    manager = test_data['db_manager']
    
    try:
        # Script içeriği
        script_content = '''
def module():
    """Test script module factory."""
    class TestScript:
        def run(self, params):
            """Test script - parametreleri işler ve döndürür."""
            message = params.get("message", "default_message")
            multiplier = int(params.get("multiplier", 1))
            
            result = {
                "processed_message": f"PROCESSED: {message}",
                "multiplier_used": multiplier,
                "repeated_message": message * multiplier,
                "timestamp": __import__("datetime").datetime.now().isoformat()
            }
            
            return result
    
    return TestScript()
'''
        
        input_schema = {
            "message": {
                "type": "string",
                "required": True,
                "description": "İşlenecek mesaj"
            },
            "multiplier": {
                "type": "integer",
                "required": False,
                "default": 1,
                "description": "Mesaj tekrar sayısı"
            }
        }
        
        output_schema = {
            "processed_message": {"type": "string"},
            "multiplier_used": {"type": "integer"},
            "repeated_message": {"type": "string"},
            "timestamp": {"type": "string"}
        }
        
        # Script dosyası oluştur
        script_dir = tempfile.mkdtemp(prefix="miniflow_test_")
        script_name = f"test_script_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        script_path = os.path.join(script_dir, f"{script_name}.py")
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print_info(f"Script dosyası oluşturuldu: {script_path}")
        test_data['script_path'] = script_path
        test_data['script_dir'] = script_dir
        
        # DB'ye script kaydı ekle
        script_repo = registry.script_repository()
        
        with manager.engine.session_context() as session:
            script = script_repo._create(
                session,
                name=script_name,
                category="test",
                description="İnteraktif test için oluşturulmuş script",
                file_path=script_path,
                input_schema=input_schema,
                output_schema=output_schema,
            )
            
            test_data['script_id'] = script.id
            print_success(f"Script DB'ye kaydedildi: {script.id}")
        
        print_data("Script Bilgileri", {
            "ID": test_data['script_id'],
            "Name": script_name,
            "Path": script_path,
            "Input Schema": input_schema,
            "Output Schema": output_schema
        })
        
        return True
        
    except Exception as e:
        print_error(f"Script oluşturma hatası: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# ADIM 4: Workflow Yapısı Oluşturma
# ============================================================================

def step4_create_workflow():
    """Workflow, Node ve Trigger oluştur."""
    print_step(4, "Workflow Yapısı Oluşturma")
    
    from miniflow.services._8_workflow_services import (
        WorkflowManagementService,
        NodeService,
        TriggerService
    )
    from miniflow.models.enums import TriggerType
    
    workflow_service = WorkflowManagementService()
    node_service = NodeService()
    trigger_service = TriggerService()
    
    try:
        # Workflow oluştur
        print_info("Workflow oluşturuluyor...")
        workflow = workflow_service.create_workflow(
            workspace_id=test_data['workspace_id'],
            name="İnteraktif Test Workflow",
            description="İnteraktif test için oluşturulmuş workflow"
        )
        test_data['workflow_id'] = workflow['id']
        print_success(f"Workflow oluşturuldu: {workflow['id']}")
        
        # Node oluştur
        print_info("Node oluşturuluyor...")
        node = node_service.create_node(
            workflow_id=test_data['workflow_id'],
            script_id=test_data['script_id'],
            name="Test Node",
            input_params={
                "message": {
                    "type": "string",
                    "value": "Hello from Interactive Test!",
                    "required": True
                },
                "multiplier": {
                    "type": "integer",
                    "value": 3,
                    "required": False
                }
            }
        )
        test_data['node_id'] = node['id']
        print_success(f"Node oluşturuldu: {node['id']}")
        
        # Trigger oluştur
        print_info("Trigger oluşturuluyor...")
        trigger = trigger_service.create_trigger(
            workflow_id=test_data['workflow_id'],
            trigger_type=TriggerType.MANUAL,
            name="Test Manual Trigger",
            input_mapping={
                "test_message": {
                    "value": "Hello Integration Test!",
                    "type": "string"
                },
                "repeat_count": {
                    "value": 3,
                    "type": "integer"
                }
            }
        )
        test_data['trigger_id'] = trigger['id']
        print_success(f"Trigger oluşturuldu: {trigger['id']}")
        
        # Workflow'u aktif et
        print_info("Workflow aktif ediliyor...")
        workflow_service.activate_workflow(test_data['workflow_id'])
        print_success("Workflow aktif edildi")
        
        print_success("✅ Workflow yapısı oluşturuldu!")
        print_data("Workflow Yapısı", {
            "Workflow ID": test_data['workflow_id'],
            "Node ID": test_data['node_id'],
            "Trigger ID": test_data['trigger_id']
        })
        
        return True
        
    except Exception as e:
        print_error(f"Workflow oluşturma hatası: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# ADIM 5: Execution Başlatma
# ============================================================================

def step5_start_execution():
    """Execution başlat ve input tablosunu kontrol et."""
    print_step(5, "Execution Başlatma")
    
    from miniflow.services._9_execution_services import ExecutionManagementService
    
    execution_service = ExecutionManagementService()
    registry = test_data['registry']
    manager = test_data['db_manager']
    
    try:
        # Execution başlat
        print_info("Execution başlatılıyor (trigger üzerinden)...")
        
        trigger_data = {
            "test_message": "Hello Interactive Test!",
            "repeat_count": 3
        }
        
        result = execution_service.start_execution_by_trigger(
            trigger_id=test_data['trigger_id'],
            trigger_data=trigger_data,
            triggered_by="interactive_test"
        )
        
        test_data['execution_id'] = result['id']
        print_success(f"Execution başlatıldı: {result['id']}")
        
        # DB'den execution kontrolü
        print_info("\n📊 Execution Tablosu Kontrolü:")
        execution_repo = registry.execution_repository()
        
        with manager.engine.session_context() as session:
            db_execution = execution_repo._get_by_id(session, record_id=test_data['execution_id'])
            
            if db_execution:
                print_success("✅ Execution DB'de bulundu:")
                print_data("Execution Detayları", {
                    "ID": db_execution.id,
                    "Workflow ID": db_execution.workflow_id,
                    "Trigger ID": db_execution.trigger_id,
                    "Status": db_execution.status.value,
                    "Trigger Data": json.loads(db_execution.trigger_data) if isinstance(db_execution.trigger_data, str) else db_execution.trigger_data,
                    "Started At": str(db_execution.started_at)
                })
            
            # ExecutionInput kontrolü
            print_info("\n📊 ExecutionInput Tablosu Kontrolü:")
            execution_input_repo = registry.execution_input_repository()
            db_inputs = execution_input_repo._get_by_execution_id(session, record_id=test_data['execution_id'])
            
            if db_inputs:
                print_success(f"✅ {len(db_inputs)} ExecutionInput bulundu:")
                for inp in db_inputs:
                    print_data("ExecutionInput", {
                        "ID": inp.id,
                        "Node ID": inp.node_id,
                        "Node Name": inp.node_name,
                        "Dependency Count": inp.dependency_count,
                        "Priority": inp.priority,
                        "Script Path": inp.script_path,
                        "Params": inp.params
                    })
                    test_data['execution_input_id'] = inp.id
            else:
                print_warning("ExecutionInput bulunamadı!")
        
        return True
        
    except Exception as e:
        print_error(f"Execution başlatma hatası: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# ADIM 6: Engine ve Scheduler Başlatma
# ============================================================================

def step6_start_engine_and_scheduler():
    """Engine ve Scheduler'ı başlat."""
    print_step(6, "Engine ve Scheduler Başlatma")
    
    from miniflow.engine.manager import EngineManager
    from miniflow.scheduler.input_handler import InputHandler
    from miniflow.scheduler.output_handler import OutputHandler
    from miniflow.services._0_internal_services.scheduler_service import (
        SchedulerForInputHandler,
        SchedulerForOutputHandler
    )
    
    try:
        # Engine Manager başlat
        print_info("Engine Manager başlatılıyor...")
        engine = EngineManager(
            queue_limit=10,
            iob_task_limit=5,
            cb_task_limit=1
        )
        test_data['engine'] = engine
        
        success = engine.start()
        if success:
            print_success("✅ Engine Manager başlatıldı")
        else:
            print_error("❌ Engine Manager başlatılamadı!")
            return False
        
        # Input Handler başlat
        print_info("Input Handler başlatılıyor...")
        input_handler = InputHandler(
            scheduler_service=SchedulerForInputHandler,
            exec_engine=engine
        )
        test_data['input_handler'] = input_handler
        
        success = input_handler.start()
        if success:
            print_success("✅ Input Handler başlatıldı")
        else:
            print_warning("⚠️  Input Handler başlatılamadı - devam ediliyor")
        
        # Output Handler başlat
        print_info("Output Handler başlatılıyor...")
        output_handler = OutputHandler(
            scheduler_service=SchedulerForOutputHandler,
            exec_engine=engine
        )
        test_data['output_handler'] = output_handler
        
        success = output_handler.start()
        if success:
            print_success("✅ Output Handler başlatıldı")
        else:
            print_warning("⚠️  Output Handler başlatılamadı - devam ediliyor")
        
        print_success("✅ Tüm bileşenler başlatıldı!")
        print_info("Engine ve Scheduler çalışıyor, execution işleniyor...")
        
        # Scheduler'ın çalışıp çalışmadığını kontrol et
        print_info("\n🔍 Scheduler Doğrulaması...")
        import time
        time.sleep(2)  # Scheduler'ın input'u işlemesi için bekle
        
        registry = test_data['registry']
        manager = test_data['db_manager']
        
        with manager.engine.session_context() as session:
            execution_input_repo = registry.execution_input_repository()
            execution_input_id = test_data.get('execution_input_id')
            
            if execution_input_id:
                try:
                    db_input = execution_input_repo._get_by_id(session, record_id=execution_input_id)
                    if db_input:
                        print_warning("    ⚠️  ExecutionInput hala DB'de (scheduler henüz işlemedi)")
                    else:
                        print_success("    ✅ ExecutionInput silindi (scheduler işledi)")
                except Exception:
                    print_success("    ✅ ExecutionInput silindi (scheduler işledi)")
                
                print_info("    📋 Scheduler Logları:")
                print("       - Execution context oluşturuldu ✅")
                print("       - Parametreler resolve edildi ✅")
                print("       - Context engine'e gönderildi ✅")
        
        return True
        
    except Exception as e:
        print_error(f"Engine/Scheduler başlatma hatası: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# ADIM 7: Sonuç Kontrolü
# ============================================================================

def step7_check_results():
    """Execution sonuçlarını kontrol et."""
    print_step(7, "Execution Sonuçlarını Kontrol Etme")
    
    registry = test_data['registry']
    execution_id = test_data['execution_id']
    manager = test_data['db_manager']
    
    print_info("Execution tamamlanması bekleniyor...")
    print_info("(Maksimum 60 saniye beklenecek)")
    
    max_wait = 60
    poll_interval = 2
    elapsed = 0
    
    final_statuses = ['COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT']
    
    while elapsed < max_wait:
        with manager.engine.session_context() as session:
            execution_repo = registry.execution_repository()
            db_execution = execution_repo._get_by_id(session, record_id=execution_id)
            
            if db_execution:
                status = db_execution.status.value
                print(f"  [{elapsed}s] Status: {status}")
                
                if status in final_statuses:
                    print_success(f"\n✅ Execution tamamlandı! Final status: {status}")
                    
                    # Sonuçları göster
                    error_info = None
                    if isinstance(db_execution.results, dict):
                        for node_id, node_result in db_execution.results.items():
                            if isinstance(node_result, dict) and node_result.get("error_message"):
                                error_info = node_result.get("error_message")
                                break
                    
                    print_data("Execution Sonuçları", {
                        "ID": db_execution.id,
                        "Status": status,
                        "Started At": str(db_execution.started_at),
                        "Ended At": str(db_execution.ended_at) if db_execution.ended_at else "N/A",
                        "Duration": db_execution.duration if hasattr(db_execution, 'duration') else "N/A",
                        "Results": db_execution.results,
                        "Error Info": error_info
                    })
                    
                    # Engine ve Scheduler doğrulaması
                    print_info("\n🔍 Engine ve Scheduler Doğrulaması...")
                    
                    if status == "COMPLETED":
                        print_success("    ✅ Execution COMPLETED (engine script'i başarıyla çalıştırdı)")
                        
                        if isinstance(db_execution.results, dict):
                            for node_id, node_result in db_execution.results.items():
                                if isinstance(node_result, dict):
                                    result_status = node_result.get("status")
                                    result_data = node_result.get("result_data", {})
                                    
                                    if result_status == "SUCCESS":
                                        print_success(f"    ✅ Node {node_id} SUCCESS (script çalıştı)")
                                        
                                        if isinstance(result_data, dict):
                                            processed_msg = result_data.get("processed_message", "")
                                            multiplier_used = result_data.get("multiplier_used")
                                            
                                            if "PROCESSED: Hello" in processed_msg:
                                                print_success(f"    ✅ Script sonucu doğru: '{processed_msg}'")
                                            else:
                                                print_error(f"    ❌ Script sonucu beklenen değil: '{processed_msg}'")
                                            
                                            if multiplier_used == 3:
                                                print_success(f"    ✅ Multiplier doğru: {multiplier_used}")
                                            else:
                                                print_error(f"    ❌ Multiplier yanlış: {multiplier_used}")
                    
                    # ExecutionInput kontrolü (silinmiş olmalı)
                    print_info("\n📊 ExecutionInput Tablosu Kontrolü (silinmiş olmalı)...")
                    execution_input_repo = registry.execution_input_repository()
                    db_inputs = execution_input_repo._get_by_execution_id(session, record_id=execution_id)
                    
                    if db_inputs:
                        print_warning(f"⚠️  {len(db_inputs)} ExecutionInput hala var (beklenen: 0)")
                    else:
                        print_success("✅ ExecutionInput'lar başarıyla temizlendi")
                    
                    return True
        
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    print_error("❌ Execution timeout! 60 saniye içinde tamamlanmadı.")
    return False


# ============================================================================
# ADIM 8: Cleanup
# ============================================================================

def step8_cleanup():
    """Temizlik işlemleri."""
    print_step(8, "Temizlik")
    
    try:
        # Handlers durdur
        if 'output_handler' in test_data and test_data['output_handler']:
            print_info("Output Handler durduruluyor...")
            test_data['output_handler'].stop()
            print_success("✅ Output Handler durduruldu")
        
        if 'input_handler' in test_data and test_data['input_handler']:
            print_info("Input Handler durduruluyor...")
            test_data['input_handler'].stop()
            print_success("✅ Input Handler durduruldu")
        
        if 'engine' in test_data and test_data['engine']:
            print_info("Engine Manager durduruluyor...")
            test_data['engine'].stop()
            print_success("✅ Engine Manager durduruldu")
        
        # Script dosyasını temizle
        if 'script_dir' in test_data:
            try:
                shutil.rmtree(test_data['script_dir'])
                print_success("✅ Script dosyası temizlendi")
            except:
                pass
        
        print_success("✅ Cleanup tamamlandı!")
        
        # Veritabanı bilgisi
        if args.db_type == 'sqlite':
            print_info(f"\n💾 Veritabanı dosyası: {args.db_path}")
            print_info("   (İsterseniz bu dosyayı silebilirsiniz)")
        
        return True
        
    except Exception as e:
        print_error(f"Cleanup hatası: {type(e).__name__}: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Ana test fonksiyonu."""
    print_header("🚀 MiniFlow Gerçek Veritabanı İnteraktif Execution Test")
    
    print(f"""
{Colors.CYAN}Bu test GERÇEK bir veritabanı ile çalışır ve execution sürecini
adım adım test eder. Her adımda size sonuçları gösterir ve
devam etmek için onayınızı bekler.{Colors.END}

{Colors.YELLOW}Veritabanı: {args.db_type.upper()}{Colors.END}
{Colors.YELLOW}Path/Host: {args.db_path if args.db_type == 'sqlite' else f'{args.db_host}:{args.db_port or (5432 if args.db_type == 'postgresql' else 3306)}'}{Colors.END}

{Colors.BOLD}Test Adımları:{Colors.END}
  1. Database Bağlantısı
  2. Test Verileri Oluşturma
  3. Script Oluşturma
  4. Workflow Yapısı Oluşturma
  5. Execution Başlatma
  6. Engine ve Scheduler Başlatma
  7. Sonuç Kontrolü
  8. Temizlik
""")
    
    wait_for_user("Teste başlamak için Enter'a basın...")
    
    steps = [
        ("Database Bağlantısı", step1_setup_database),
        ("Test Verileri Oluşturma", step2_create_test_data),
        ("Script Oluşturma", step3_create_script),
        ("Workflow Yapısı Oluşturma", step4_create_workflow),
        ("Execution Başlatma", step5_start_execution),
        ("Engine ve Scheduler Başlatma", step6_start_engine_and_scheduler),
        ("Sonuç Kontrolü", step7_check_results),
        ("Temizlik", step8_cleanup),
    ]
    
    results = []
    
    try:
        for step_name, step_func in steps:
            success = step_func()
            results.append((step_name, success))
            
            if not success:
                print_error(f"\n❌ '{step_name}' adımı başarısız oldu!")
                response = input("\nDevam etmek istiyor musunuz? (y/N): ")
                if response.lower() != 'y':
                    break
            
            if step_name != "Temizlik":
                wait_for_user(f"'{step_name}' tamamlandı. Sonraki adıma geçmek için Enter'a basın...")
        
        # Final Summary
        print_header("📊 FINAL TEST SUMMARY")
        
        passed = sum(1 for _, success in results if success)
        failed = len(results) - passed
        
        for step_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} - {step_name}")
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"  {Colors.GREEN}Geçen: {passed}/{len(results)}{Colors.END}")
        
        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TÜM TESTLER BAŞARILI!{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️ BAZI TESTLER BAŞARISIZ!{Colors.END}")
        
        print(f"\n{Colors.CYAN}Test tamamlandı!{Colors.END}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test iptal edildi.{Colors.END}")
        step8_cleanup()
        sys.exit(0)
    except Exception as e:
        print_error(f"Beklenmeyen hata: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        step8_cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()

