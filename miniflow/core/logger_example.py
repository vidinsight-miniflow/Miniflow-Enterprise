"""
LOGGER KULLANIM ÖRNEKLERİ
========================

Bu dosya, miniflow.core.logger modülünün nasıl kullanılacağını gösterir.
"""

# Örnek 1: Temel Kullanım
# -----------------------
from miniflow.core.logger import get_logger

# Her modülde kendi logger'ını al
logger = get_logger(__name__)

# Farklı seviyeler
logger.debug("Debug bilgisi - sadece development'ta görünür")
logger.info("Normal bilgi mesajı")
logger.warning("Dikkat edilmesi gereken durum")
logger.error("Hata oluştu")
logger.critical("Kritik sistem hatası")


# Örnek 2: Exception Logging
# --------------------------
def risky_operation():
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        # Stack trace ile birlikte logla
        logger.error(f"Division hatası: {e}", exc_info=True)
        raise


# Örnek 3: Function Decorator
# ---------------------------
from miniflow.core.logger import log_function_call

@log_function_call
def calculate_workflow_cost(workflow_id: int, execution_time: float) -> float:
    """
    Workflow maliyetini hesapla.
    
    Decorator otomatik olarak şunları loglar:
    - Fonksiyon çağrısı
    - Parametreler
    - Dönüş değeri
    - Exception'lar (varsa)
    """
    cost_per_second = 0.001
    return execution_time * cost_per_second


# Örnek 4: Context Manager
# ------------------------
from miniflow.core.logger import log_exception

def database_operation():
    with log_exception(logger):
        # Bu blok içinde oluşan tüm exception'lar otomatik loglanır
        # connection = database.connect()
        # connection.execute("INSERT INTO ...")
        pass


# Örnek 5: Yapılandırma (main.py'de)
# ----------------------------------
from miniflow.core.logger import configure_root_logger
import logging

# Development ortamı
configure_root_logger(
    level=logging.DEBUG,
    console_output=True  # Hem dosyaya hem console'a
)

# Production ortamı
configure_root_logger(
    level=logging.WARNING,
    console_output=False  # Sadece dosyaya
)


# Örnek 6: Modül Bazlı Logger
# ---------------------------
# src/miniflow/database/engine.py
db_logger = get_logger("miniflow.database")
db_logger.info("Database connection established")

# src/miniflow/api/routes.py
api_logger = get_logger("miniflow.api")
api_logger.info("API request received")

# src/miniflow/executor/workflow.py
executor_logger = get_logger("miniflow.executor")
executor_logger.error("Workflow execution failed")


# Örnek 7: Detaylı Hata Loglama
# -----------------------------
def process_workflow(workflow_id: int):
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Processing workflow {workflow_id}")
        
        # İşlem adımları
        logger.debug(f"Loading workflow {workflow_id} from database")
        # workflow = load_workflow(workflow_id)
        
        logger.debug(f"Validating workflow {workflow_id}")
        # validate(workflow)
        
        logger.debug(f"Executing workflow {workflow_id}")
        # result = execute(workflow)
        
        logger.info(f"Workflow {workflow_id} completed successfully")
        
    except ValueError as e:
        logger.error(
            f"Validation error for workflow {workflow_id}: {e}",
            exc_info=True
        )
        raise
    
    except ConnectionError as e:
        logger.critical(
            f"Database connection lost while processing workflow {workflow_id}: {e}",
            exc_info=True
        )
        raise
    
    except Exception as e:
        logger.critical(
            f"Unexpected error processing workflow {workflow_id}: {e}",
            exc_info=True
        )
        raise


# Örnek 8: İstatistikler
# ----------------------
from miniflow.core.logger import get_log_stats, get_log_files

def show_log_stats():
    stats = get_log_stats()
    print(f"Toplam log dosyası: {stats['total_files']}")
    print(f"Toplam boyut: {stats['total_size_mb']:.2f} MB")
    
    for file_info in stats['files']:
        print(f"  {file_info['name']}: {file_info['size_mb']:.2f} MB")


# Örnek 9: Ortam Değişkenleri
# ---------------------------
# .env dosyasında:
# LOG_LEVEL=DEBUG
# APP_ENV=development

# Logger otomatik olarak bu değişkenleri okur:
# - LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL
# - APP_ENV: development, production, test


# Örnek 10: Gerçek Senaryo - API Endpoint
# ---------------------------------------
from miniflow.core.logger import get_logger

api_logger = get_logger("miniflow.api.workflows")

def create_workflow_endpoint(request):
    """POST /api/workflows endpoint"""
    
    api_logger.info(f"Workflow creation request received from {request.user_id}")
    
    try:
        # Request validation
        api_logger.debug(f"Validating request data: {request.data}")
        validate_workflow_data(request.data)
        
        # Database operation
        api_logger.debug("Creating workflow in database")
        workflow = create_workflow(request.data)
        
        api_logger.info(
            f"Workflow created successfully: "
            f"id={workflow.id}, name={workflow.name}, user={request.user_id}"
        )
        
        return {"success": True, "workflow_id": workflow.id}
        
    except ValidationError as e:
        api_logger.warning(
            f"Workflow validation failed for user {request.user_id}: {e}"
        )
        return {"success": False, "error": str(e)}
        
    except DatabaseError as e:
        api_logger.error(
            f"Database error while creating workflow for user {request.user_id}: {e}",
            exc_info=True
        )
        return {"success": False, "error": "Internal server error"}
        
    except Exception as e:
        api_logger.critical(
            f"Unexpected error in workflow creation for user {request.user_id}: {e}",
            exc_info=True
        )
        return {"success": False, "error": "Internal server error"}


# ÖZET
# ====
# 
# 1. Her modülde: logger = get_logger(__name__)
# 2. Exception'larda: logger.error("msg", exc_info=True)
# 3. Decorator için: @log_function_call
# 4. Context manager: with log_exception(logger):
# 5. Yapılandırma: configure_root_logger() (main.py'de)
# 
# Log dosyaları: logs/miniflow.log (maksimum 5 dosya, her biri 10MB)

