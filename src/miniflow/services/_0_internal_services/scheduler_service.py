import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import ExecutionStatus
from miniflow.core.exceptions import ResourceNotFoundError, InvalidInputError
from miniflow.core.logger import get_logger
from miniflow.utils.helpers.encryption_helper import decrypt_data
from miniflow.utils.handlers.configuration_handler import ConfigurationHandler
from miniflow.utils.helpers.file_helper import get_workspace_file_path


logger = get_logger(__name__)


_registry = RepositoryRegistry()
_execution_input_repo = _registry.execution_input_repository()
_execution_repo = _registry.execution_repository()
_execution_output_repo = _registry.execution_output_repository()
_variable_repo = _registry.variable_repository()
_credential_repo = _registry.credential_repository()
_database_repo = _registry.database_repository()
_file_repo = _registry.file_repository()
_edge_repo = _registry.edge_repository()
_workflow_repo = _registry.workflow_repository()


class TypeConverter:
    @staticmethod
    def to_string(param_name: str, param_value: Any):
        """
        Parametre değerini string tipine dönüştürür.
        
        Args:
            param_name (str): Parametre adı, hata mesajlarında kullanılır. resolve_parameters'dan gelir.
            param_value (Any): Dönüştürülecek değer, reference resolver'dan veya static değerden gelir.
        
        Returns:
            str: Dönüştürülmüş string değer.
        """
        if isinstance(param_value, str):
            return param_value
        
        try:
            return str(param_value)
        except Exception as e:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Cannot convert {type(param_value).__name__} to string. ",
                )

    @staticmethod
    def to_integer(param_name: str, param_value: Any):
        """
        Parametre değerini integer tipine dönüştürür.
        
        Args:
            param_name (str): Parametre adı, hata mesajlarında kullanılır. resolve_parameters'dan gelir.
            param_value (Any): Dönüştürülecek değer, reference resolver'dan veya static değerden gelir.
        
        Returns:
            int: Dönüştürülmüş integer değer.
        """
        if isinstance(param_value, int):
            return param_value
        
        try:
            return int(param_value)
        except Exception as e:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Cannot convert {type(param_value).__name__} to integer. ",
                )

    @staticmethod
    def to_float(param_name: str, param_value: Any):
        """
        Parametre değerini float tipine dönüştürür.
        
        Args:
            param_name (str): Parametre adı, hata mesajlarında kullanılır. resolve_parameters'dan gelir.
            param_value (Any): Dönüştürülecek değer, reference resolver'dan veya static değerden gelir.
        
        Returns:
            float: Dönüştürülmüş float değer.
        """
        if isinstance(param_value, float):
            return param_value
        
        try:
            return float(param_value)
        except Exception as e:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Cannot convert {type(param_value).__name__} to float. ",
                )

    @staticmethod
    def to_boolean(param_name: str, param_value: Any):
        """
        Parametre değerini boolean tipine dönüştürür.
        
        Args:
            param_name (str): Parametre adı, hata mesajlarında kullanılır. resolve_parameters'dan gelir.
            param_value (Any): Dönüştürülecek değer, reference resolver'dan veya static değerden gelir.
        
        Returns:
            bool: Dönüştürülmüş boolean değer.
        """
        if isinstance(param_value, bool):
            return param_value

        if isinstance(param_value, (str, int, float)):
                val_str = str(param_value).lower().strip()
                if val_str in ("true", "1", "yes", "on"):
                    return True
                if val_str in ("false", "0", "no", "off", ""):
                    return False
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Type conversion failed for '{param_name}': "
                            f"Cannot convert {type(param_value).__name__} to boolean. "
                            f"Valid true values: true, 1, yes, on. "
                            f"Valid false values: false, 0, no, off, empty string."
                    )

    @staticmethod
    def to_array(param_name: str, param_value: Any):
        """
        Parametre değerini array/list tipine dönüştürür.
        
        Args:
            param_name (str): Parametre adı, hata mesajlarında kullanılır. resolve_parameters'dan gelir.
            param_value (Any): Dönüştürülecek değer, reference resolver'dan veya static değerden gelir.
        
        Returns:
            list: Dönüştürülmüş list değer.
        """
        if isinstance(param_value, list):
            return param_value
        
        try:
            parsed_value = json.loads(param_value)
            if not isinstance(parsed_value, list):
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Type conversion failed for '{param_name}': "
                            f"JSON parsed successfully but result is {type(parsed_value).__name__}, not list. "
                )
            return parsed_value
        except Exception as e:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Cannot parse JSON array from string. "
                        f"JSON Error: {str(e)}"
                )

    @staticmethod
    def to_object(param_name: str, param_value: Any):
        """
        Parametre değerini object/dict tipine dönüştürür.
        
        Args:
            param_name (str): Parametre adı, hata mesajlarında kullanılır. resolve_parameters'dan gelir.
            param_value (Any): Dönüştürülecek değer, reference resolver'dan veya static değerden gelir.
        
        Returns:
            dict: Dönüştürülmüş dict değer.
        """
        if isinstance(param_value, dict):
            return param_value
        
        try:
            parsed_value = json.loads(param_value)
            if not isinstance(parsed_value, dict):
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Type conversion failed for '{param_name}': "
                            f"JSON parsed successfully but result is {type(parsed_value).__name__}, not dict. "
                )
            return parsed_value
        except Exception as e:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Cannot parse JSON object from string. "
                        f"JSON Error: {str(e)}"
                )

class RefrenceResolver:
    @classmethod
    def _get_type_groups(cls):
        """TYPE_GROUPS'u configuration'dan dinamik olarak yükler."""
        ConfigurationHandler.ensure_loaded()
        return {
            "string": ConfigurationHandler.get_list("SCHEDULER_SERVICE", "accepted_string_values", fallback=["string", "text", "str"]),
            "integer": ConfigurationHandler.get_list("SCHEDULER_SERVICE", "accepted_integer_values", fallback=["number", "integer", "int"]),
            "float": ConfigurationHandler.get_list("SCHEDULER_SERVICE", "accepted_float_values", fallback=["float"]),
            "boolean": ConfigurationHandler.get_list("SCHEDULER_SERVICE", "accepted_boolean_values", fallback=["bool", "boolean"]),
            "array": ConfigurationHandler.get_list("SCHEDULER_SERVICE", "accepted_array_values", fallback=["array", "list"]),
            "object": ConfigurationHandler.get_list("SCHEDULER_SERVICE", "accepted_object_values", fallback=["object", "dict", "json"]),
        }

    @staticmethod
    def _resolve_nested_reference(value_path: str) -> list:
        """
        İç içe referans yolunu parçalara ayırır (örn: "data.items[0].name").
        
        Args:
            value_path (str): Nested path string, reference_info["value_path"]'den gelir.
                             Örnek: "data.items[0].name", "result.data", "api_key"
        
        Returns:
            list: Parçalara ayrılmış liste. Örnek: ["data", "items", "[0]", "name"]
        
        Girdi:
            value_path: "data.items[0].name"  # Nested path string
        
        Çıktı:
            ["data", "items", "[0]", "name"]  # Parçalara ayrılmış liste
        """
        if not value_path:
            return []
        
        parts = re.split(r'(\[.*?\])', value_path)  
        parts = [p for p in parts if p]
    
        final_parts = []
        for part in parts:
            if part.startswith("[") and part.endswith("]"):
                final_parts.append(part)
            else:
                keys = part.split(".")
                final_parts.extend(keys)
        final_parts = [p for p in final_parts if p]
        return final_parts
        
    @staticmethod
    def _get_value_from_context(path_parts: list, context: Any):
        """
        Parçalara ayrılmış yol ile context'ten değer çıkarır.
        
        Args:
            path_parts (list): Parçalara ayrılmış yol, _resolve_nested_reference'dan gelir.
                              Örnek: ["data", "items", "[0]", "name"]
            context (Any): Dict veya list, reference resolver metodlarından gelir.
                          Örnek: ExecutionOutput.result_data, Execution.trigger_data, File metadata
        
        Returns:
            Any: Yoldan çıkarılan değer. Örnek: "test", 123, {"key": "value"}
        
        Girdi:
            path_parts: ["data", "items", "[0]", "name"]  # Parçalara ayrılmış yol
            context: {"data": {"items": [{"name": "test"}]}}  # Dict veya list
        
        Çıktı:
            "test"  # Yoldan çıkarılan değer
        """
        if path_parts == []:
            return context
        
        if not isinstance(context, (dict, list)):
            raise InvalidInputError(message=f"Cannot resolve path '{path_parts}' on non-nested data type: {type(context).__name__}")
        
        current_data = context
        for path_part in path_parts:
            if path_part.startswith("[") and path_part.endswith("]"):
                if not isinstance(current_data, list):
                    raise InvalidInputError(message=f"Cannot access array index '{path_part}' on non-list data")
                try:
                    index = int(path_part[1:-1])
                    if index < 0 or index >= len(current_data):
                        raise InvalidInputError(message=f"Array index '{index}' out of range (length: {len(current_data)})")
                    current_data = current_data[index]
                except ValueError:
                    raise InvalidInputError(message=f"Invalid array index: {path_part}")
            else:
                if path_part not in current_data:
                    raise InvalidInputError(message=f"Key '{path_part}' not found in data")   
                current_data = current_data[path_part]
        return current_data            

    @classmethod
    def _convert_to_type(cls, param_name: str, param_value: Any, expected_type: str) -> Any:
        """
        Parametre değerini beklenen tipe dönüştürür.
        
        Args:
            param_name (str): Parametre adı, reference_info["param_name"]'den gelir.
            param_value (Any): Dönüştürülecek değer, _get_value_from_context veya static değerden gelir.
            expected_type (str): Beklenen tip, reference_info["expected_type"]'dan gelir.
                               Geçerli değerler: "string", "integer", "float", "boolean", "array", "object"
        
        Returns:
            Any: Dönüştürülmüş değer. Tip expected_type'a göre değişir.
        
        Girdi:
            param_name: "timeout"  # Parametre adı
            param_value: "30"  # Dönüştürülecek değer
            expected_type: "integer"  # Beklenen tip
        
        Çıktı:
            30  # Dönüştürülmüş değer (integer)
        """
        expected_type = expected_type.lower().strip()
        
        # Normalize type aliases
        type_mapping = {
            "integer": "int",
            "number": "int",
            "text": "str",
            "list": "array",
            "dict": "object",
            "json": "object"
        }
        if expected_type in type_mapping:
            expected_type = type_mapping[expected_type]
        
        type_groups = cls._get_type_groups()
        
        if expected_type in type_groups["string"]:
            return TypeConverter.to_string(param_name, param_value)
        elif expected_type in type_groups["integer"]:
            return TypeConverter.to_integer(param_name, param_value)
        elif expected_type in type_groups["float"]:
            return TypeConverter.to_float(param_name, param_value)
        elif expected_type in type_groups["boolean"]:
            return TypeConverter.to_boolean(param_name, param_value)
        elif expected_type in type_groups["array"]:
            return TypeConverter.to_array(param_name, param_value)
        elif expected_type in type_groups["object"]:
            return TypeConverter.to_object(param_name, param_value)
        else:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Unknown target type '{expected_type}'. "
                        f"Valid types: string, text, str, number, integer, int, float, "
                        f"boolean, bool, array, list, object, dict, json."
            )

    @classmethod
    def get_static_data(cls, reference_info: Dict[str, Any]):
        """
        Statik referans değerini getirir ve tip dönüşümü yapar.
        
        Args:
            reference_info (Dict[str, Any]): Referans bilgileri, resolve_refrences'dan gelir.
                - id_or_value (str): Statik değer, _parse_refrence'dan gelir.
                - param_name (str): Parametre adı, _parse_refrence'dan gelir.
                - expected_type (str): Beklenen tip, _parse_refrence'dan gelir.
        
        Returns:
            Any: Dönüştürülmüş değer (expected_type'a göre)
        
        Girdi:
            reference_info: {
                "id_or_value": "değer",  # Statik değer
                "param_name": "param_adı",
                "expected_type": "string"  # string, integer, float, boolean, array, object
            }
        
        Çıktı:
            Dönüştürülmüş değer (expected_type'a göre)
        """
        value = reference_info.get("id_or_value")
        param_name = reference_info.get("param_name")
        expected_type = reference_info.get("expected_type", "string")
        return cls._convert_to_type(param_name, value, expected_type)
    
    @classmethod
    @with_transaction(manager=None)
    def get_trigger_data(cls, session, reference_info: Dict[str, Any]):
        """
        Trigger referansından değeri getirir ve tip dönüşümü yapar.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            reference_info (Dict[str, Any]): Referans bilgileri, resolve_refrences'dan gelir.
                - execution_id (str): Execution ID, resolve_parameters'dan gelir.
                - value_path (str, optional): Nested path, _parse_refrence'dan gelir.
                - param_name (str): Parametre adı, _parse_refrence'dan gelir.
                - expected_type (str): Beklenen tip, _parse_refrence'dan gelir.
        
        Returns:
            Any: Execution.trigger_data'dan çıkarılan ve dönüştürülmüş değer
        
        Girdi:
            reference_info: {
                "execution_id": "EXE-...",
                "value_path": "data.items[0].name",  # Opsiyonel, nested path
                "param_name": "param_adı",
                "expected_type": "string"
            }
        
        Çıktı:
            Execution.trigger_data'dan çıkarılan ve dönüştürülmüş değer
        """
        path = reference_info.get("value_path")
        execution_id = reference_info["execution_id"]
        param_name = reference_info.get("param_name")
        expected_type = reference_info.get("expected_type", "string")

        execution = _execution_repo._get_by_id(session, record_id=execution_id, include_deleted=False)
        if not execution:
            raise ResourceNotFoundError(
                resource_name="Execution", resource_id=execution_id)
        
        trigger_data = execution.trigger_data or {}
        path_parts = cls._resolve_nested_reference(path) if path else []
        value = cls._get_value_from_context(path_parts, trigger_data)
        
        return cls._convert_to_type(param_name, value, expected_type)
    
    @classmethod
    @with_transaction(manager=None)
    def get_executed_node_data(cls, session, reference_info: Dict[str, Any]):
        """
        Çalıştırılmış node'un çıktı verisinden değeri getirir ve tip dönüşümü yapar.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            reference_info (Dict[str, Any]): Referans bilgileri, resolve_refrences'dan gelir.
                - id (str): Node ID, _parse_refrence'dan gelir.
                - execution_id (str): Execution ID, resolve_parameters'dan gelir.
                - value_path (str, optional): Nested path, _parse_refrence'dan gelir.
                - param_name (str): Parametre adı, _parse_refrence'dan gelir.
                - expected_type (str): Beklenen tip, _parse_refrence'dan gelir.
        
        Returns:
            Any: ExecutionOutput.result_data'dan çıkarılan ve dönüştürülmüş değer
        
        Girdi:
            reference_info: {
                "id": "NOD-...",  # Node ID
                "execution_id": "EXE-...",
                "value_path": "result.data",  # Opsiyonel, nested path
                "param_name": "param_adı",
                "expected_type": "string"
            }
        
        Çıktı:
            ExecutionOutput.result_data'dan çıkarılan ve dönüştürülmüş değer
        """
        id = reference_info.get("id") or reference_info.get("id_or_value")
        path = reference_info.get("value_path")
        execution_id = reference_info["execution_id"]
        param_name = reference_info.get("param_name")
        expected_type = reference_info.get("expected_type", "string")

        if not id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Node reference requires 'id' or 'id_or_value' field"
            )

        execution_output = _execution_output_repo._get_by_execution_and_node(session, execution_id=execution_id, node_id=id, include_deleted=False)
        if not execution_output:
            raise ResourceNotFoundError(
                resource_name="ExecutionOutput", resource_id=id)
        
        node_data = execution_output.result_data or {}
        path_parts = cls._resolve_nested_reference(path) if path else []
        value = cls._get_value_from_context(path_parts, node_data)
        
        return cls._convert_to_type(param_name, value, expected_type)

    @classmethod
    @with_transaction(manager=None)
    def get_variable_data(cls, session, reference_info: Dict[str, Any]):
        """
        Variable referansından değeri getirir, şifreli ise çözer ve tip dönüşümü yapar.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            reference_info (Dict[str, Any]): Referans bilgileri, resolve_refrences'dan gelir.
                - id (str): Variable ID, _parse_refrence'dan gelir.
                - workspace_id (str): Workspace ID, resolve_parameters'dan gelir.
                - param_name (str): Parametre adı, _parse_refrence'dan gelir.
                - expected_type (str): Beklenen tip, _parse_refrence'dan gelir.
        
        Returns:
            Any: Variable.value'dan alınan (şifreli ise çözülmüş) ve dönüştürülmüş değer
        
        Girdi:
            reference_info: {
                "id": "ENV-...",  # Variable ID
                "workspace_id": "WSP-...",
                "param_name": "param_adı",
                "expected_type": "string"
            }
        
        Çıktı:
            Variable.value'dan alınan (şifreli ise çözülmüş) ve dönüştürülmüş değer
        """
        id = reference_info.get("id") or reference_info.get("id_or_value")
        workspace_id = reference_info["workspace_id"]
        param_name = reference_info.get("param_name")
        expected_type = reference_info.get("expected_type", "string")

        if not id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Variable reference requires 'id' or 'id_or_value' field"
            )

        variable = _variable_repo._get_by_id(session, record_id=id, include_deleted=False)
        if not variable:
            raise ResourceNotFoundError(
                resource_name="Variable", resource_id=id)
        
        if variable.workspace_id != workspace_id:
            raise InvalidInputError(field_name=param_name, message=f"Variable '{id}' does not belong to workspace '{workspace_id}'")
        
        if variable.is_secret:
            value = decrypt_data(variable.value)
        else:
            value = variable.value

        return cls._convert_to_type(param_name, value, expected_type)

    @classmethod
    @with_transaction(manager=None)
    def get_database_data(cls, session, reference_info: Dict[str, Any]):
        """
        Database referansından bağlantı bilgilerini getirir, şifreyi çözer ve tip dönüşümü yapar.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            reference_info (Dict[str, Any]): Referans bilgileri, resolve_refrences'dan gelir.
                - id (str): Database ID, _parse_refrence'dan gelir.
                - workspace_id (str): Workspace ID, resolve_parameters'dan gelir.
                - value_path (str, optional): Nested path, _parse_refrence'dan gelir.
                  Geçerli değerler: "host", "port", "username", "password", "database_name", 
                  "connection_string", "ssl_enabled", "additional_params"
                - param_name (str): Parametre adı, _parse_refrence'dan gelir.
                - expected_type (str): Beklenen tip, _parse_refrence'dan gelir.
        
        Returns:
            Any: Database bağlantı bilgisinden çıkarılan (password çözülmüş) ve dönüştürülmüş değer
        
        Girdi:
            reference_info: {
                "id": "DBS-...",  # Database ID
                "workspace_id": "WSP-...",
                "value_path": "host",  # Opsiyonel: host, port, username, password, database_name, connection_string, ssl_enabled, additional_params
                "param_name": "param_adı",
                "expected_type": "string"
            }
        
        Çıktı:
            Database bağlantı bilgisinden çıkarılan (password çözülmüş) ve dönüştürülmüş değer
        """
        id = reference_info.get("id") or reference_info.get("id_or_value")
        path = reference_info.get("value_path")
        workspace_id = reference_info["workspace_id"]
        param_name = reference_info.get("param_name")
        expected_type = reference_info.get("expected_type", "string")

        if not id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Database reference requires 'id' or 'id_or_value' field"
            )

        database = _database_repo._get_by_id(session, record_id=id, include_deleted=False)
        if not database:
            raise ResourceNotFoundError(
                resource_name="Database", resource_id=id)

        if database.workspace_id != workspace_id:
            raise InvalidInputError(field_name=param_name, message=f"Database '{id}' does not belong to workspace '{workspace_id}'")
        
        password = getattr(database, "password", None)
        if password:
            try:
                password = decrypt_data(password)
            except Exception as e:
                logger.warning(
                    f"Failed to decrypt password for database '{id}' (workspace: {workspace_id}): {str(e)}. "
                    f"Continuing with encrypted password."
                )
        
        database_data = {
            "host": getattr(database, "host", None),
            "port": getattr(database, "port", None),
            "username": getattr(database, "username", None),
            "password": password,
            "database_name": getattr(database, "database_name", None),
            "connection_string": database.connection_string,
            "ssl_enabled": database.ssl_enabled,
            "additional_params": database.additional_params
        }

        path_parts = cls._resolve_nested_reference(path) if path else []
        value = cls._get_value_from_context(path_parts, database_data)
        
        return cls._convert_to_type(param_name, value, expected_type)

    @classmethod
    @with_transaction(manager=None)
    def get_file_data(cls, session, reference_info: Dict[str, Any]):
        """
        File referansından dosya bilgilerini veya içeriğini getirir ve tip dönüşümü yapar.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            reference_info (Dict[str, Any]): Referans bilgileri, resolve_refrences'dan gelir.
                - id (str): File ID, _parse_refrence'dan gelir.
                - workspace_id (str): Workspace ID, resolve_parameters'dan gelir.
                - value_path (str, optional): Nested path, _parse_refrence'dan gelir.
                  "content" ise dosya içeriği okunur, diğer durumlarda metadata'dan değer çıkarılır.
                  Geçerli değerler: "content", "name", "file_size", "mime_type", "file_extension", 
                  "description", "tags", "file_metadata"
                - param_name (str): Parametre adı, _parse_refrence'dan gelir.
                - expected_type (str): Beklenen tip, _parse_refrence'dan gelir.
        
        Returns:
            Any: value_path="content" ise dosya içeriği (string), 
                 diğer durumlarda dosya metadata'sından çıkarılan ve dönüştürülmüş değer
        
        Girdi:
            reference_info: {
                "id": "FLE-...",  # File ID
                "workspace_id": "WSP-...",
                "value_path": "content" veya "name", "file_size", "mime_type" vb.,  # Opsiyonel
                "param_name": "param_adı",
                "expected_type": "string"
            }
        
        Çıktı:
            - value_path="content" ise: Dosya içeriği (string)
            - Diğer durumlarda: Dosya metadata'sından çıkarılan ve dönüştürülmüş değer
        """
        id = reference_info.get("id") or reference_info.get("id_or_value")
        path = reference_info.get("value_path")
        workspace_id = reference_info["workspace_id"]
        param_name = reference_info.get("param_name")
        expected_type = reference_info.get("expected_type", "string")

        if not id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"File reference requires 'id' or 'id_or_value' field"
            )

        file_obj = _file_repo._get_by_id(session, record_id=id, include_deleted=False)
        if not file_obj:
            raise ResourceNotFoundError(
                resource_name="File", resource_id=id)
        
        if file_obj.workspace_id != workspace_id:
            raise InvalidInputError(field_name=param_name, message=f"File '{id}' does not belong to workspace '{workspace_id}'")
        
        if path and path == "content":
            try:
                logger.debug(f"Reading file content: file_id={id}, file_path={file_obj.file_path}")
                with open(file_obj.file_path, 'r', encoding='utf-8') as f:
                    value = f.read()
                logger.debug(f"File content read successfully: file_id={id}, size={len(value)} bytes")
            except Exception as e:
                logger.error(f"Failed to read file content: file_id={id}, file_path={file_obj.file_path}, error={str(e)}")
                raise InvalidInputError(field_name=param_name ,message=f"Failed to read file content: {str(e)}")
        else:
            file_data = {
                "name": file_obj.name,
                "original_filename": file_obj.original_filename,
                "file_size": file_obj.file_size,
                "mime_type": file_obj.mime_type,
                "file_extension": file_obj.file_extension,
                "description": file_obj.description,
                "tags": file_obj.tags,
                "file_metadata": file_obj.file_metadata
            }

            path_parts = cls._resolve_nested_reference(path) if path else []
            value = cls._get_value_from_context(path_parts, file_data)
        
        return cls._convert_to_type(param_name, value, expected_type)

    @classmethod
    @with_transaction(manager=None)
    def get_credential_data(cls, session, reference_info: Dict[str, Any]):
        """
        Credential referansından kimlik bilgilerini getirir, şifreyi çözer ve tip dönüşümü yapar.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            reference_info (Dict[str, Any]): Referans bilgileri, resolve_refrences'dan gelir.
                - id (str): Credential ID, _parse_refrence'dan gelir.
                - workspace_id (str): Workspace ID, resolve_parameters'dan gelir.
                - value_path (str, optional): Nested path, _parse_refrence'dan gelir.
                  credential_data içinde nested path ile değer çıkarılır.
                - param_name (str): Parametre adı, _parse_refrence'dan gelir.
                - expected_type (str): Beklenen tip, _parse_refrence'dan gelir.
        
        Returns:
            Any: Credential.credential_data'dan çıkarılan (şifre çözülmüş) ve dönüştürülmüş değer
        
        Girdi:
            reference_info: {
                "id": "CRD-...",  # Credential ID
                "workspace_id": "WSP-...",
                "value_path": "api_key",  # Opsiyonel, nested path (credential_data içinde)
                "param_name": "param_adı",
                "expected_type": "string"
            }
        
        Çıktı:
            Credential.credential_data'dan çıkarılan (şifre çözülmüş) ve dönüştürülmüş değer
        """
        id = reference_info.get("id") or reference_info.get("id_or_value")
        path = reference_info.get("value_path")
        workspace_id = reference_info["workspace_id"]
        param_name = reference_info.get("param_name")
        expected_type = reference_info.get("expected_type", "string")

        if not id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Credential reference requires 'id' or 'id_or_value' field"
            )

        credential = _credential_repo._get_by_id(session, record_id=id, include_deleted=False)
        if not credential:
            raise ResourceNotFoundError(
                resource_name="Credential", resource_id=id)
        
        if credential.workspace_id != workspace_id:
            raise InvalidInputError(field_name=param_name, message=f"Credential '{id}' does not belong to workspace '{workspace_id}'")
        
        credential_data = decrypt_data(credential.credential_data)
        path_parts = cls._resolve_nested_reference(path) if path else []
        value = cls._get_value_from_context(path_parts, credential_data)

        return cls._convert_to_type(param_name, value, expected_type)


class SchedulerForInputHandler:
    """
    Input Handler için scheduler metodları.
    
    Lifecycle:
    1. get_ready_execution_inputs() -> İşlenmeye hazır input'ları getirir
    2. create_execution_context() -> Her input için execution context oluşturur
       - resolve_parameters() -> Parametreleri referans tipine göre gruplar
       - resolve_refrences() -> Tüm referansları çözer
    3. remove_processed_execution_inputs() -> İşlenen input'ları siler
    """

    @classmethod
    @with_transaction(manager=None)
    def get_ready_execution_inputs(
        cls,
        session,
        *,
        batch_size: int = 20
    ) -> Dict[str, Any]:
        """
        İşlenmeye hazır execution input'ları getirir ve kalanların wait_factor'ını artırır.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            batch_size (int, optional): Kaç input seçileceği, default 20. Scheduler'dan gelir.
        
        Returns:
            Dict[str, Any]: {
                "count": 15,  # Seçilen input sayısı
                "ids": ["EXI-123", "EXI-456", ...]  # Seçilen input ID'leri
            }
        
        Girdi:
            batch_size: 20  # Kaç input seçilecek
        
        Çıktı:
            {
                "count": 15,  # Seçilen input sayısı
                "ids": ["EXI-123", "EXI-456", ...]  # Seçilen input ID'leri
            }
        """
        all_ready_inputs = _execution_input_repo._get_ready_execution_inputs(session)

        selected_inputs = all_ready_inputs[:batch_size]
        remaining_inputs = all_ready_inputs[batch_size:]
        
        if remaining_inputs:
            remaining_ids = [inp.id for inp in remaining_inputs]
            _execution_input_repo._increment_wait_factor_by_ids(
                session,
                execution_input_ids=remaining_ids
            )
        
        return {
            "count": len(selected_inputs),
            "ids": [inp.id for inp in selected_inputs]
        }
    
    @staticmethod
    def _is_reference(value: str) -> bool:
        """
        Değerin referans formatında olup olmadığını kontrol eder (${type:...}).
        
        Args:
            value (str): Kontrol edilecek değer, params dict'inden gelir.
                        Örnek: "${node:NOD-123.result}" veya "static_value"
        
        Returns:
            bool: True (referans ise) veya False (değilse)
        
        Girdi:
            value: "${node:NOD-123.result}" veya "static_value"
        
        Çıktı:
            True (referans ise) veya False (değilse)
        """
        if not isinstance(value, str):
            return False
        if not (value.startswith("${") and value.endswith("}")):
            return False
        if ":" not in value:
            return False
    
        return True

    @staticmethod
    def _parse_refrence(refrence: str, param_name: str, expected_type: str) -> Dict[str, Any]:
        """
        Referans string'ini parse eder ve referans bilgilerini döndürür.
        
        Args:
            refrence (str): Referans string'i, params dict'inden gelir.
                           Örnek: "${node:NOD-123.result.data}", "${credential:CRD-456.api_key}"
            param_name (str): Parametre adı, params dict'inin key'inden gelir.
            expected_type (str): Beklenen tip, params dict'inin "type" değerinden gelir.
                               Örnek: "string", "integer", "float", "boolean", "array", "object"
        
        Returns:
            Dict[str, Any]: Parse edilmiş referans bilgileri. Örnek:
                {
                    "type": "node",
                    "id": "NOD-123",
                    "value_path": "result.data",
                    "param_name": "timeout",
                    "expected_type": "integer"
                }
        
        Girdi:
            refrence: "${node:NOD-123.result.data}"
            param_name: "timeout"
            expected_type: "integer"
        
        Çıktı:
            {
                "type": "node",
                "id": "NOD-123",
                "value_path": "result.data",
                "param_name": "timeout",
                "expected_type": "integer"
            }
        """
        content = refrence[2:-1]
        ref_type, identifier_path = content.split(":", 1)

        ref_type = ref_type.strip()
        identifier_path = identifier_path.strip()

        valid_types = ["static", "trigger", "node", "value", "credential", "database", "file"]
        if ref_type not in valid_types:
            raise InvalidInputError(message=f"Invalid reference type '{ref_type}'. Valid types: {', '.join(valid_types)}")
        
        id_or_value = None
        value_path = None

        if ref_type == "static":
            id_or_value = identifier_path
            value_path = None
        elif ref_type == "trigger":
            id_or_value = None
            value_path = identifier_path
        elif ref_type in ["node", "value", "credential", "database", "file"]:
            if "." in identifier_path:
                parts = identifier_path.split(".", 1)
                id_or_value = parts[0]
                value_path = parts[1]
            else:
                id_or_value = identifier_path
                value_path = None
        else:
            raise InvalidInputError(message=f"Invalid reference type '{ref_type}'. Valid types: {', '.join(valid_types)}")
        
        result = {
            "type": ref_type,
            "param_name": param_name,
            "expected_type": expected_type
        }
        
        if ref_type == "static":
            result["id_or_value"] = id_or_value
            result["value_path"] = None
        elif ref_type == "trigger":
            result["id"] = None
            result["value_path"] = value_path
        else:
            result["id"] = id_or_value
            result["value_path"] = value_path
        
        return result

    @classmethod
    def resolve_parameters(
        cls, 
        workspace_id: str,
        execution_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Parametreleri referans tipine göre gruplara ayırır.
        
        Args:
            workspace_id (str): Workspace ID, ExecutionInput.workspace_id'den gelir.
            execution_id (str): Execution ID, ExecutionInput.execution_id'den gelir.
            params (Dict[str, Any]): Parametreler dict'i, ExecutionInput.params'dan gelir.
                                    Format: {"param_name": {"value": "...", "type": "..."}}
        
        Returns:
            Dict[str, Any]: Referans tipine göre gruplanmış referans bilgileri.
                          Format: {"static": [...], "trigger": [...], "node": [...], ...}
        
        Girdi:
            workspace_id: "WSP-..."
            execution_id: "EXE-..."
            params: {
                "timeout": {"value": "${node:NOD-123.result}", "type": "integer"},
                "api_key": {"value": "${credential:CRD-456.api_key}", "type": "string"},
                "static_val": {"value": "test", "type": "string"}
            }
        
        Çıktı:
            {
                "static": [...],
                "trigger": [...],
                "node": [{"type": "node", "id": "NOD-123", ...}],
                "credential": [{"type": "credential", "id": "CRD-456", ...}],
                ...
            }
        """
        groups = {
            "static": [],
            "trigger": [],
            "node": [],
            "value": [],
            "credential": [],
            "database": [],
            "file": []
        }

        for param_name, param_data in params.items():
            param_value = param_data.get('value')
            expected_type = param_data.get('type')

            if cls._is_reference(param_value):
                reference_info = cls._parse_refrence(param_value, param_name, expected_type)
                reference_info['workspace_id'] = workspace_id
                reference_info['execution_id'] = execution_id
                ref_type = reference_info["type"]
                groups[ref_type].append(reference_info)
            else:
                groups['static'].append({
                    "type": 'static',
                    "id_or_value": param_value,
                    "value_path": None,
                    "param_name": param_name,
                    "expected_type": expected_type
                })

        return groups

    @classmethod
    def resolve_refrences(
        cls,
        groups: Dict[str, List[Dict[str, Any]]],
        session
    ) -> Dict[str, Any]:
        """
        Gruplanmış referansları çözer ve resolved parametreler döndürür.
        
        Args:
            groups (Dict[str, List[Dict[str, Any]]]): Referans tipine göre gruplanmış referans bilgileri,
                                                     resolve_parameters'dan gelir.
            session: Database session, create_execution_context'dan gelir (@with_transaction'dan).
        
        Returns:
            Dict[str, Any]: Çözülmüş parametreler dict'i. Key: param_name, Value: çözülmüş ve dönüştürülmüş değer.
        
        Girdi:
            groups: {
                "node": [{"type": "node", "id": "NOD-123", "param_name": "timeout", ...}],
                "credential": [{"type": "credential", "id": "CRD-456", "param_name": "api_key", ...}],
                ...
            }
            session: Database session
        
        Çıktı:
            {
                "timeout": 30,  # Çözülmüş ve dönüştürülmüş değer
                "api_key": "secret_key",  # Çözülmüş ve dönüştürülmüş değer
                ...
            }
        """
        resolved_params = {}

        for ref_info in groups.get("static", []):
            value = RefrenceResolver.get_static_data(ref_info)
            resolved_params[ref_info["param_name"]] = value

        for ref_info in groups.get("trigger", []):
            value = RefrenceResolver.get_trigger_data(ref_info)
            resolved_params[ref_info["param_name"]] = value

        for ref_info in groups.get("node", []):
            value = RefrenceResolver.get_executed_node_data(ref_info)
            resolved_params[ref_info["param_name"]] = value

        for ref_info in groups.get("value", []):
            value = RefrenceResolver.get_variable_data(ref_info)
            resolved_params[ref_info["param_name"]] = value

        for ref_info in groups.get("credential", []):
            value = RefrenceResolver.get_credential_data(ref_info)
            resolved_params[ref_info["param_name"]] = value

        for ref_info in groups.get("database", []):
            value = RefrenceResolver.get_database_data(ref_info)
            resolved_params[ref_info["param_name"]] = value

        for ref_info in groups.get("file", []):
            value = RefrenceResolver.get_file_data(ref_info)
            resolved_params[ref_info["param_name"]] = value

        return resolved_params

    @classmethod
    @with_transaction(manager=None)
    def create_execution_context(
        cls,
        session,
        execution_input_id: str,
    ) -> Dict[str, Any]:
        """
        Execution input'tan execution context oluşturur ve tüm referansları çözer.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            execution_input_id (str): ExecutionInput ID, get_ready_execution_inputs'dan gelen ID'lerden biri.
        
        Returns:
            Dict[str, Any]: Execution context dict'i. Engine'e gönderilecek format.
                - execution_id (str): Execution ID
                - workspace_id (str): Workspace ID
                - workflow_id (str): Workflow ID
                - node_id (str): Node ID
                - script_path (str): Script dosya yolu
                - params (Dict[str, Any]): Çözülmüş parametreler
                - max_retries (int): Maksimum retry sayısı
                - timeout_seconds (int): Timeout süresi (saniye)
        
        Girdi:
            execution_input_id: "EXI-..."  # ExecutionInput ID
        
        Çıktı:
            {
                "execution_id": "EXE-...",
                "workspace_id": "WSP-...",
                "workflow_id": "WFL-...",
                "node_id": "NOD-...",
                "script_path": "/path/to/script.py",
                "params": {
                    "timeout": 30,  # Çözülmüş parametreler
                    "api_key": "secret",
                    ...
                },
                "max_retries": 3,
                "timeout_seconds": 300
            }
        """
        logger.info(f"Creating execution context for execution_input_id: {execution_input_id}")
        
        execution_input = _execution_input_repo._get_by_id(session, record_id=execution_input_id, include_deleted=False)
        if not execution_input:
            logger.error(f"ExecutionInput not found: {execution_input_id}")
            raise ResourceNotFoundError(
                resource_name="ExecutionInput", resource_id=execution_input_id)
        
        execution_id = execution_input.execution_id
        workspace_id = execution_input.workspace_id
        workflow_id = execution_input.workflow_id
        node_id = execution_input.node_id
        params = execution_input.params or {}

        logger.debug(f"Resolving parameters for execution_id: {execution_id}, node_id: {node_id}, params_count: {len(params)}")
        groups = cls.resolve_parameters(workspace_id, execution_id, params)

        logger.debug(f"Resolving references: {sum(len(v) for v in groups.values())} total references")
        resolved_params = cls.resolve_refrences(groups, session)
        
        for param_name, param_data in params.items():
            if param_name not in resolved_params:
                value = param_data.get("value")
                if not (isinstance(value, str) and cls._is_reference(value)):
                    resolved_params[param_name] = value
        
        context = {
            "execution_id": execution_id,
            "workspace_id": workspace_id,
            "workflow_id": workflow_id,
            "node_id": node_id,
            "script_path": execution_input.script_path,
            "params": resolved_params,
            "max_retries": execution_input.max_retries,
            "timeout_seconds": execution_input.timeout_seconds
        }
        
        logger.info(f"Execution context created successfully for execution_id: {execution_id}, node_id: {node_id}, resolved_params_count: {len(resolved_params)}")
        return context

    @classmethod
    @with_transaction(manager=None)
    def remove_processed_execution_inputs(
        cls,
        session,
        execution_input_ids: List[str]
    ) -> int:
        """
        İşlenmiş execution input'ları toplu olarak siler.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            execution_input_ids (List[str]): Silinecek ExecutionInput ID'leri listesi,
                                           get_ready_execution_inputs'dan gelen ID'lerden oluşur.
        
        Returns:
            int: Silinen kayıt sayısı
        
        Girdi:
            execution_input_ids: ["EXI-123", "EXI-456", ...]  # Silinecek input ID'leri
        
        Çıktı:
            5  # Silinen kayıt sayısı
        """
        return _execution_input_repo._delete_by_ids(
            session, 
            execution_input_ids=execution_input_ids
        )

class SchedulerForOutputHandler:
    """
    Output Handler için scheduler metodları.
    
    Lifecycle:
    1. process_execution_result() -> Engine'den gelen result'ı alır ve status'e göre yönlendirir
       - FAILED ise:
         -> _handle_failed_node()
           -> _collect_and_delete_execution_inputs() -> Input'ları topla, dict oluştur, sil
           -> _collect_and_delete_execution_outputs() -> Output'ları topla, dict oluştur, sil
           -> _update_execution_with_results() -> Execution'ı FAILED olarak güncelle
       - SUCCESS ise:
         -> _handle_successful_node()
           -> _create_execution_output_record() -> Output kaydı oluştur
           -> _is_last_node() -> Son düğüm kontrolü
           - Son düğümse:
             -> _collect_and_delete_execution_outputs() -> Output'ları topla, dict oluştur, sil
             -> _update_execution_with_results() -> Execution'ı COMPLETED olarak güncelle
           - Son düğüm değilse:
             -> _decrement_next_nodes_dependencies() -> Sonraki düğümlerin dependency_count'unu azalt
    """
    
    @classmethod
    @with_transaction(manager=None)
    def process_execution_result(
        cls,
        session,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Engine'den gelen execution result'ı işler ve status'e göre yönlendirir.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            result (Dict[str, Any]): Engine'den gelen execution result dict'i.
                - execution_id (str): Execution ID, zorunlu
                - node_id (str): Node ID, zorunlu
                - status (str): "SUCCESS" veya "FAILED", zorunlu
                - result_data (Dict, optional): Node çıktı verisi (SUCCESS durumunda)
                - started_at (datetime, optional): Başlangıç zamanı
                - ended_at (datetime, optional): Bitiş zamanı
                - memory_mb (float, optional): Kullanılan bellek (MB)
                - cpu_percent (float, optional): CPU kullanım yüzdesi
                - error_message (str, optional): Hata mesajı (FAILED durumunda)
                - error_details (Dict, optional): Hata detayları (FAILED durumunda)
        
        Returns:
            Dict[str, Any]: İşlem sonucu.
                FAILED ise: {"execution_id": "...", "status": "FAILED", "processed": True}
                SUCCESS ise: {"execution_id": "...", "execution_output_id": "...", "is_last_node": bool, ...}
        
        Girdi:
            result: {
                "execution_id": "EXE-...",
                "node_id": "NOD-...",
                "status": "SUCCESS" veya "FAILED",
                "result_data": {...},
                "started_at": datetime,
                "ended_at": datetime,
                "memory_mb": 256.0,
                "cpu_percent": 50.0,
                "error_message": "...",
                "error_details": {...}
            }
        
        Çıktı:
            FAILED ise: {"execution_id": "...", "status": "FAILED", "processed": True}
            SUCCESS ise: {"execution_id": "...", "execution_output_id": "...", "is_last_node": bool, ...}
        """
        execution_id = result.get("execution_id")
        status = result.get("status")
        node_id = result.get("node_id")
        
        logger.info(f"Processing execution result: execution_id={execution_id}, node_id={node_id}, status={status}")
        
        if not execution_id:
            logger.error("execution_id is missing in result payload")
            raise InvalidInputError(
                field_name="execution_id",
                message="execution_id is required in result payload"
            )
        
        if not status:
            logger.error(f"status is missing in result payload for execution_id: {execution_id}")
            raise InvalidInputError(
                field_name="status",
                message="status is required in result payload"
            )
        
        execution = _execution_repo._get_by_id(session, record_id=execution_id, include_deleted=False)
        if not execution:
            logger.error(f"Execution not found: {execution_id}")
            raise ResourceNotFoundError(
                resource_name="Execution", resource_id=execution_id)
        
        if status == "FAILED":
            logger.warning(f"Node execution failed: execution_id={execution_id}, node_id={node_id}")
            return cls._handle_failed_node(session, result, execution)
        elif status == "SUCCESS":
            logger.debug(f"Node execution succeeded: execution_id={execution_id}, node_id={node_id}")
            return cls._handle_successful_node(session, result, execution)
        else:
            raise InvalidInputError(
                field_name="status",
                message=f"Invalid status '{status}'. Expected 'SUCCESS' or 'FAILED'"
            )
    
    @classmethod
    def _handle_failed_node(
        cls,
        session,
        result: Dict[str, Any],
        execution
    ) -> Dict[str, Any]:
        """
        Başarısız node durumunu işler: input ve output'ları toplar, siler ve execution'ı günceller.
        
        Args:
            session: Database session, process_execution_result'dan gelir (transaction içinde).
            result (Dict[str, Any]): Engine'den gelen result dict'i, process_execution_result'dan gelir.
            execution: Execution objesi, process_execution_result'da cache'lenmiş.
        
        Returns:
            Dict[str, Any]: {"execution_id": "...", "status": "FAILED", "processed": True}
        
        Girdi:
            result: {"execution_id": "...", "node_id": "...", "status": "FAILED", ...}
            execution: Execution objesi (cache'lenmiş)
        
        Çıktı:
            {"execution_id": "...", "status": "FAILED", "processed": True}
        """
        execution_id = execution.id
        node_id = result.get("node_id")
        
        if not node_id:
            raise InvalidInputError(
                field_name="node_id",
                message="node_id is required in result payload for FAILED status"
            )
        
        cancelled_dict = cls._collect_and_delete_execution_inputs(
            session, execution_id, failed_node_id=node_id
        )
        
        outputs_dict = cls._collect_and_delete_execution_outputs(session, execution_id)
        
        merged_results = {**outputs_dict, **cancelled_dict}
        cls._update_execution_with_results(
            session, execution, ExecutionStatus.FAILED, merged_results
        )
        
        return {
            "execution_id": execution_id,
            "status": "FAILED",
            "processed": True
        }
    
    @classmethod
    def _handle_successful_node(
        cls,
        session,
        result: Dict[str, Any],
        execution
    ) -> Dict[str, Any]:
        """
        Başarılı node durumunu işler: output kaydı oluşturur, son düğüm kontrolü yapar ve dependency günceller.
        
        Args:
            session: Database session, process_execution_result'dan gelir (transaction içinde).
            result (Dict[str, Any]): Engine'den gelen result dict'i, process_execution_result'dan gelir.
            execution: Execution objesi, process_execution_result'da cache'lenmiş.
        
        Returns:
            Dict[str, Any]: Son düğümse: {"execution_id": "...", "execution_output_id": "...", "is_last_node": True, "execution_completed": True}
                           Değilse: {"execution_id": "...", "execution_output_id": "...", "is_last_node": False, "updated_dependencies": 2}
        
        Girdi:
            result: {"execution_id": "...", "node_id": "...", "status": "SUCCESS", ...}
            execution: Execution objesi (cache'lenmiş)
        
        Çıktı:
            Son düğümse: {"execution_id": "...", "execution_output_id": "...", "is_last_node": True, "execution_completed": True}
            Değilse: {"execution_id": "...", "execution_output_id": "...", "is_last_node": False, "updated_dependencies": 2}
        """
        execution_id = execution.id
        node_id = result.get("node_id")
        workflow_id = execution.workflow_id
        
        if not node_id:
            raise InvalidInputError(
                field_name="node_id",
                message="node_id is required in result payload for SUCCESS status"
            )
        
        execution_output_id = cls._create_execution_output_record(session, result, execution)
        
        outgoing_edges = _edge_repo._get_by_from_node_id(
            session, workflow_id=workflow_id, from_node_id=node_id, include_deleted=False
        )
        
        is_last = cls._is_last_node(outgoing_edges)
        
        if is_last:
            outputs_dict = cls._collect_and_delete_execution_outputs(session, execution_id)
            cls._update_execution_with_results(
                session, execution, ExecutionStatus.COMPLETED, outputs_dict
            )
            
            return {
                "execution_id": execution_id,
                "execution_output_id": execution_output_id,
                "is_last_node": True,
                "execution_completed": True
            }
        else:
            updated_count = cls._decrement_next_nodes_dependencies(
                session, execution_id, node_id, outgoing_edges
            )
            
            return {
                "execution_id": execution_id,
                "execution_output_id": execution_output_id,
                "is_last_node": False,
                "updated_dependencies": updated_count
            }
    
    @classmethod
    def _collect_and_delete_execution_inputs(
        cls,
        session,
        execution_id: str,
        failed_node_id: str
    ) -> Dict[str, Any]:
        """
        Execution input'ları toplar, iptal edilmiş dict oluşturur ve siler.
        
        Args:
            session: Database session, _handle_failed_node'dan gelir (transaction içinde).
            execution_id (str): Execution ID, _handle_failed_node'dan gelir.
            failed_node_id (str): Başarısız olan node ID, result["node_id"]'den gelir.
        
        Returns:
            Dict[str, Any]: Node ID'ye göre gruplanmış iptal edilmiş input'lar dict'i.
                          Format: {"NOD-123": {"status": "CANCELLED", "error_message": "...", ...}, ...}
        
        Girdi:
            execution_id: "EXE-..."
            failed_node_id: "NOD-..."  # Başarısız olan node ID
        
        Çıktı:
            {
                "NOD-123": {
                    "status": "CANCELLED",
                    "error_message": "Cancelled because of failed node: NOD-...",
                    ...
                },
                ...
            }
        """
        inputs = _execution_input_repo._get_by_execution_id(
            session, record_id=execution_id, include_deleted=False
        )
        
        cancelled_dict = {}
        for input_obj in inputs:
            if input_obj.node_id:
                cancelled_dict[input_obj.node_id] = {
                    'status': ExecutionStatus.CANCELLED.value,
                    'result_data': None,
                    'memory_mb': None,
                    'cpu_percent': None,
                    'duration_seconds': None,
                    'error_message': f'Cancelled because of failed node: {failed_node_id}',
                    'error_details': {'failed_node_id': failed_node_id}
                }
        
        _execution_input_repo._delete_by_execution_id(session, execution_id=execution_id)
        
        return cancelled_dict
    
    @classmethod
    def _collect_and_delete_execution_outputs(
        cls,
        session,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Execution output'ları toplar, dict oluşturur ve siler.
        
        Args:
            session: Database session, _handle_failed_node veya _handle_successful_node'dan gelir (transaction içinde).
            execution_id (str): Execution ID, _handle_failed_node veya _handle_successful_node'dan gelir.
        
        Returns:
            Dict[str, Any]: Node ID'ye göre gruplanmış output'lar dict'i.
                          Format: {"NOD-123": {"status": "SUCCESS", "result_data": {...}, ...}, ...}
        
        Girdi:
            execution_id: "EXE-..."
        
        Çıktı:
            {
                "NOD-123": {
                    "status": "SUCCESS",
                    "result_data": {...},
                    "memory_mb": 256.0,
                    "cpu_percent": 50.0,
                    ...
                },
                ...
            }
        """
        outputs = _execution_output_repo._get_by_execution_id(
            session, record_id=execution_id, include_deleted=False
        )
        
        outputs_dict = {}
        for output in outputs:
            if output.node_id:
                outputs_dict[output.node_id] = {
                    'status': output.status,
                    'result_data': output.result_data or {},
                    'memory_mb': output.memory_mb,
                    'cpu_percent': output.cpu_percent,
                    'duration_seconds': output.duration,
                    'error_message': output.error_message,
                    'error_details': output.error_details or {}
                }
        
        _execution_output_repo._delete_by_execution_id(session, execution_id=execution_id)
        
        return outputs_dict
    
    @classmethod
    def _is_last_node(
        cls,
        outgoing_edges: List
    ) -> bool:
        """
        Node'un son düğüm olup olmadığını kontrol eder (outgoing edge yoksa son düğümdür).
        
        Args:
            outgoing_edges (List): Bu node'dan çıkan edge'ler listesi,
                                 _edge_repo._get_by_from_node_id'dan gelir.
        
        Returns:
            bool: True (son düğümse, outgoing_edges boş) veya False (değilse)
        
        Girdi:
            outgoing_edges: [Edge(...), Edge(...)]  # Bu node'dan çıkan edge'ler
        
        Çıktı:
            True (son düğümse) veya False (değilse)
        """
        return len(outgoing_edges) == 0
    
    @classmethod
    def _create_execution_output_record(
        cls,
        session,
        result: Dict[str, Any],
        execution
    ):
        """
        Engine'den gelen result'tan execution output kaydı oluşturur.
        
        Args:
            session: Database session, parent transaction'dan gelir.
            result (Dict[str, Any]): Engine'den gelen result dict'i, _handle_successful_node'dan gelir.
            execution: Execution objesi, _handle_successful_node'da cache'lenmiş.
        
        Returns:
            str: Oluşturulan ExecutionOutput'un ID'si.
        
        Girdi:
            result: {"execution_id": "...", "node_id": "...", "status": "SUCCESS", "result_data": {...}, ...}
            execution: Execution objesi (cache'lenmiş)
        
        Çıktı:
            "EXOUT-..." (oluşturulan ExecutionOutput ID'si)
        """
        status = result.get("status", "SUCCESS")
        node_id = result.get("node_id")
        
        if not node_id:
            raise InvalidInputError(
                field_name="node_id",
                message="node_id is required in result payload"
            )
        
        started_at = result.get("started_at")
        if started_at:
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elif not isinstance(started_at, datetime):
                started_at = None
        
        ended_at = result.get("ended_at")
        if ended_at:
            if isinstance(ended_at, str):
                ended_at = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
            elif not isinstance(ended_at, datetime):
                ended_at = datetime.now(timezone.utc)
        else:
            ended_at = datetime.now(timezone.utc)
        
        execution_output = _execution_output_repo._create(
            session,
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            workspace_id=execution.workspace_id,
            node_id=node_id,
            status=status,
            result_data=result.get("result_data", {}),
            started_at=started_at,
            ended_at=ended_at,
            memory_mb=result.get("memory_mb"),
            cpu_percent=result.get("cpu_percent"),
            error_message=result.get("error_message"),
            error_details=result.get("error_details", {}),
            retry_count=result.get("retry_count", 0)
        )
        
        # Extract the ID while session is still active to avoid DetachedInstanceError
        session.flush()  # Ensure the object is persisted and has an ID
        output_id = execution_output.id
        
        return output_id
    
    @classmethod
    def _decrement_next_nodes_dependencies(
        cls,
        session,
        execution_id: str,
        completed_node_id: str,
        outgoing_edges: List
    ) -> int:
        """
        Tamamlanan node'un sonraki düğümlerinin dependency_count değerlerini batch olarak azaltır.
        
        Args:
            session: Database session, _handle_successful_node'dan gelir (transaction içinde).
            execution_id (str): Execution ID, _handle_successful_node'dan gelir.
            completed_node_id (str): Tamamlanan node ID, result["node_id"]'den gelir.
            outgoing_edges (List): Bu node'dan çıkan edge'ler listesi,
                                 _edge_repo._get_by_from_node_id'dan gelir.
        
        Returns:
            int: Güncellenen dependency sayısı (batch update sonucu)
        
        Girdi:
            execution_id: "EXE-..."
            completed_node_id: "NOD-..."  # Tamamlanan node ID
            outgoing_edges: [Edge(...), Edge(...)]  # Bu node'dan çıkan edge'ler
        
        Çıktı:
            2  # Güncellenen dependency sayısı
        """
        if not outgoing_edges:
            return 0
        
        target_node_ids = [edge.to_node_id for edge in outgoing_edges]
        
        updated_count = _execution_input_repo._decrement_dependency_count_by_node_ids(
            session,
            execution_id=execution_id,
            node_ids=target_node_ids
        )
        
        return updated_count
    
    @classmethod
    def _update_execution_with_results(
        cls,
        session,
        execution,
        status: ExecutionStatus,
        results: Dict[str, Any]
    ):
        """
        Execution'ı sonuçlarla günceller ve durumunu değiştirir.
        
        Args:
            session: Database session, @with_transaction decorator'ından gelir.
            execution: Execution objesi, _handle_failed_node veya _handle_successful_node'da cache'lenmiş.
            status (ExecutionStatus): Yeni execution durumu, ExecutionStatus.FAILED veya ExecutionStatus.COMPLETED.
            results (Dict[str, Any]): Node ID'ye göre gruplanmış sonuçlar dict'i.
                                    _collect_and_delete_execution_inputs veya _collect_and_delete_execution_outputs'dan gelir.
                                    Format: {"NOD-123": {"status": "...", "result_data": {...}, ...}, ...}
        
        Returns:
            Execution: Güncellenmiş Execution objesi
        
        Girdi:
            execution: Execution objesi (cache'lenmiş)
            status: ExecutionStatus.FAILED veya ExecutionStatus.COMPLETED
            results: {
                "NOD-123": {"status": "SUCCESS", "result_data": {...}, ...},
                "NOD-456": {"status": "CANCELLED", ...},
                ...
            }
        
        Çıktı:
            Güncellenmiş Execution objesi
        """
        execution.status = status
        execution.ended_at = datetime.now(timezone.utc)
        execution.results = results
        
        session.add(execution)
        
        return execution

