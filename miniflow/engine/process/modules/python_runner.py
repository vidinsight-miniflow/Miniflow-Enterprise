import importlib.util
import json
import traceback
from datetime import datetime, timezone
from queue import Queue


def python_runner(item: json, output_queue: Queue):
    execution_id = item.get("execution_id", "UNKNOWN")
    node_id = item.get("node_id", "UNKNOWN")

    print(f"[PYTHON_RUNNER] Starting task: execution_id={execution_id}, node_id={node_id}")
    
    started_at = datetime.now(timezone.utc)
    item["started_at"] = started_at.isoformat()
    
    try:
        script_path = item.get("script_path")
        if not script_path:
            raise ValueError("script_path is missing")

        module_name = script_path.split("/")[-1].replace(".py", "")

        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for module at {script_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "module"):
            raise AttributeError("The module must contain a 'module()' function")

        run_module = module.module()

        if not hasattr(run_module, "run"):
            raise AttributeError("The object returned by 'module()' must have a 'run()' method")

        # Script parametrelerini al (flat yapıda)
        params = item.get("params", {})

        # Eğer params string ise JSON parse et
        if isinstance(params, str):
            params = json.loads(params)

        result = run_module.run(params)
        
        item["result_data"] = result
        item["status"] = "SUCCESS"

    except FileNotFoundError as e:
        item["error_message"] = "Script file not found"
        item["error_details"] = {"exception_type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        item["status"] = "FAILED"
    except ImportError as e:
        item["error_message"] = f"Import error: {str(e)}"
        item["error_details"] = {"exception_type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        item["status"] = "FAILED"
    except AttributeError as e:
        item["error_message"] = f"Attribute error: {str(e)}"
        item["error_details"] = {"exception_type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        item["status"] = "FAILED"
    except ValueError as e:
        item["error_message"] = f"Value error: {str(e)}"
        item["error_details"] = {"exception_type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        item["status"] = "FAILED"
    except (json.JSONDecodeError, TypeError) as e:
        item["error_message"] = f"JSON error: {str(e)}"
        item["error_details"] = {"exception_type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        item["status"] = "FAILED"
    except Exception as e:
        item["error_message"] = f"Unexpected error: {str(e)}"
        item["error_details"] = {"exception_type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        item["status"] = "FAILED"
    finally:
        ended_at = datetime.now(timezone.utc)
        item["ended_at"] = ended_at.isoformat()

    output_queue.put(item)
