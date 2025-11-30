import json
import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.models.enums import ExecutionStatus
from src.miniflow.core.exceptions import ResourceNotFoundError, InvalidInputError
from src.miniflow.utils.helpers.encryption_helper import decrypt_data
from src.miniflow.utils.helpers.file_helper import get_workspace_file_path


class SchedulerService:
    def __init__(self):
        self._registry = RepositoryRegistry()
        self._execution_input_repo = self._registry.execution_input_repository
        self._execution_repo = self._registry.execution_repository
        self._execution_output_repo = self._registry.execution_output_repository
        self._variable_repo = self._registry.variable_repository
        self._credential_repo = self._registry.credential_repository
        self._database_repo = self._registry.database_repository
        self._file_repo = self._registry.file_repository
        self._edge_repo = self._registry.edge_repository
        self._workflow_repo = self._registry.workflow_repository

    @with_transaction(manager=None)
    def get_ready_execution_inputs(self, session, *, batch_size: int = 20) -> Dict[str, Any]:
        """
        Get ready execution inputs that can be processed.
        """

        all_ready_inputs = self._execution_input_repo._get_ready_execution_inputs(session)
        
        selected_inputs = all_ready_inputs[:batch_size]
        remaining_inputs = all_ready_inputs[batch_size:]
        
        if remaining_inputs:
            remaining_ids = [inp.id for inp in remaining_inputs]
            self._execution_input_repo._increment_wait_factor_by_ids(
                session,
                execution_input_ids=remaining_ids
            )
        
        return {
            "count": len(selected_inputs),
            "ids": [inp.id for inp in selected_inputs]
        }

    def _is_reference(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        if not (value.startswith("${") and value.endswith("}")):
            return False
        if ":" not in value:
            return False
    
        return True
   
    def _parse_reference(self, reference_str: str, param_name: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
        content = reference_str[2:-1]
        ref_type, identifier_path = content.split(":", 1)
        ref_type = ref_type.strip()
        identifier_path = identifier_path.strip()

        valid_types = ["static", "trigger", "node", "value", "credential", "database", "file"]
        if ref_type not in valid_types:
            raise InvalidInputError(
                message=f"Invalid reference type '{ref_type}'. Valid types: {', '.join(valid_types)}"
            )
        
        ref_id = None
        path = None
        
        if ref_type == "static":
            ref_id = identifier_path
            path = None
        elif ref_type == "trigger":
            ref_id = None
            path = identifier_path
        elif ref_type in ["node", "value", "credential", "database", "file"]:
            if "." in identifier_path:
                parts = identifier_path.split(".", 1)
                ref_id = parts[0]
                path = parts[1]
            else:
                ref_id = identifier_path
                path = None
        else:
            raise InvalidInputError(
                message=f"Invalid reference type '{ref_type}'. Valid types: {', '.join(valid_types)}"
            )
        
        return {
            "type": ref_type,
            "id": ref_id,
            "path": path,
            "param_name": param_name,
            "expected_type": expected_type
        }

    def resolve_parameters(self, params: Dict[str, Any]):
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
            value = param_data.get("value")
            expected_type = param_data.get("type", "string")

            if isinstance(value, str) and self._is_reference(value):
                reference_info = self._parse_reference(value, param_name, expected_type)
                ref_type = reference_info["type"]
                groups[ref_type].append(reference_info)

        return groups


    """
    {
        "static": [
            {
                "type": "static",
                "id": "30",
                "path": None,
                "param_name": "timeout",
                "expected_type": "number"
            }
        ],
        "trigger": [
            {
                "type": "trigger",
                "id": None,
                "path": "user.email.value",
                "param_name": "user_email",
                "expected_type": "string"
            }
        ],
        "credential": [
            {
                "type": "credential",
                "id": "CRD-789",
                "path": "api_key",
                "param_name": "api_key",
                "expected_type": "string"
            }
        ],
        "value": [
            {
                "type": "value",
                "id": "ENV-456",
                "path": "admin_email",
                "param_name": "admin_email",
                "expected_type": "string"
            }
        ],
        "node": [],
        "database": [],
        "file": []
    }
    """
    def _convert_to_type(self, value: Any, expected_type: str, param_name: str) -> Any:
        """
        Value'yu expected_type'a dönüştür.
        
        Desteklenen tipler:
        - string, text, str: Metin
        - number, integer, int: Tam sayı
        - float: Ondalıklı sayı
        - boolean, bool: Mantıksal değer
        - array, list: Liste/dizi
        - object, dict, json: Sözlük/nesne
        
        Hata durumunda InvalidInputError fırlatılır ve:
        - Parametre adı
        - Beklenen tip
        - Gelen değerin tipi
        - Gelen değerin kendisi (güvenli şekilde)
        açıkça belirtilir.
        """
        if value is None:
            return None
    
        type_lower = expected_type.lower()
        value_type = type(value).__name__
        
        # Güvenli değer gösterimi (çok uzun veya karmaşık değerler için)
        def _safe_value_repr(val, max_length=100):
            repr_str = repr(val)
            if len(repr_str) > max_length:
                return repr_str[:max_length] + "..."
            return repr_str

        # === STRING ===
        if type_lower in ("string", "text", "str"):
            if isinstance(value, str):
                return value
            # Diğer tipleri string'e çevir
            try:
                return str(value)
            except Exception as e:
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Type conversion failed for '{param_name}': "
                            f"Cannot convert {value_type} to string. "
                            f"Value: {_safe_value_repr(value)}. Error: {str(e)}"
                )

        # === INTEGER / NUMBER ===
        elif type_lower in ("number", "integer", "int"):
            # Zaten int veya float ise
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return int(value)
            
            # String ise parse et
            if isinstance(value, str):
                cleaned_value = value.strip()
                if not cleaned_value:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Type conversion failed for '{param_name}': "
                                f"Expected integer but got empty string."
                    )
                try:
                    return int(float(cleaned_value))
                except (ValueError, TypeError) as e:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Type conversion failed for '{param_name}': "
                                f"Cannot convert string '{cleaned_value}' to integer. "
                                f"Error: {str(e)}"
                    )
            
            # Desteklenmeyen tip
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Expected integer but got {value_type}. "
                        f"Value: {_safe_value_repr(value)}. "
                        f"Supported input types: int, float, numeric string."
            )

        # === FLOAT ===
        elif type_lower == "float":
            # Zaten int veya float ise
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
            
            # String ise parse et
            if isinstance(value, str):
                cleaned_value = value.strip()
                if not cleaned_value:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Type conversion failed for '{param_name}': "
                                f"Expected float but got empty string."
                    )
                try:
                    return float(cleaned_value)
                except (ValueError, TypeError) as e:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Type conversion failed for '{param_name}': "
                                f"Cannot convert string '{cleaned_value}' to float. "
                                f"Error: {str(e)}"
                    )
            
            # Desteklenmeyen tip
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Expected float but got {value_type}. "
                        f"Value: {_safe_value_repr(value)}. "
                        f"Supported input types: int, float, numeric string."
            )

        # === BOOLEAN ===
        elif type_lower in ("boolean", "bool"):
            # Zaten bool ise
            if isinstance(value, bool):
                return value
            
            # String veya sayı ise parse et
            if isinstance(value, (str, int, float)):
                val_str = str(value).lower().strip()
                if val_str in ("true", "1", "yes", "on"):
                    return True
                if val_str in ("false", "0", "no", "off", ""):
                    return False
                
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Type conversion failed for '{param_name}': "
                            f"Cannot convert '{val_str}' to boolean. "
                            f"Valid true values: true, 1, yes, on. "
                            f"Valid false values: false, 0, no, off, empty string."
                )
            
            # Desteklenmeyen tip
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Expected boolean but got {value_type}. "
                        f"Value: {_safe_value_repr(value)}. "
                        f"Supported input types: bool, string, int."
            )

        # === ARRAY / LIST ===
        elif type_lower in ("array", "list"):
            # Zaten list ise
            if isinstance(value, list):
                return value
            
            # String ise JSON parse et
            if isinstance(value, str):
                cleaned_value = value.strip()
                if not cleaned_value:
                    return []
                try:
                    parsed = json.loads(cleaned_value)
                    if not isinstance(parsed, list):
                        raise InvalidInputError(
                            field_name=param_name,
                            message=f"Type conversion failed for '{param_name}': "
                                    f"JSON parsed successfully but result is {type(parsed).__name__}, not list. "
                                    f"Value: {_safe_value_repr(value)}"
                        )
                    return parsed
                except json.JSONDecodeError as e:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Type conversion failed for '{param_name}': "
                                f"Cannot parse JSON array from string. "
                                f"Value: {_safe_value_repr(value)}. "
                                f"JSON Error: {str(e)}"
                    )
            
            # Desteklenmeyen tip
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Expected array but got {value_type}. "
                        f"Value: {_safe_value_repr(value)}. "
                        f"Supported input types: list, JSON array string."
            )

        # === OBJECT / DICT / JSON ===
        elif type_lower in ("object", "dict", "json"):
            # Zaten dict ise
            if isinstance(value, dict):
                return value
            
            # String ise JSON parse et
            if isinstance(value, str):
                cleaned_value = value.strip()
                if not cleaned_value:
                    return {}
                try:
                    parsed = json.loads(cleaned_value)
                    if not isinstance(parsed, dict):
                        raise InvalidInputError(
                            field_name=param_name,
                            message=f"Type conversion failed for '{param_name}': "
                                    f"JSON parsed successfully but result is {type(parsed).__name__}, not dict. "
                                    f"Value: {_safe_value_repr(value)}"
                        )
                    return parsed
                except json.JSONDecodeError as e:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Type conversion failed for '{param_name}': "
                                f"Cannot parse JSON object from string. "
                                f"Value: {_safe_value_repr(value)}. "
                                f"JSON Error: {str(e)}"
                    )
            
            # Desteklenmeyen tip
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Expected object/dict but got {value_type}. "
                        f"Value: {_safe_value_repr(value)}. "
                        f"Supported input types: dict, JSON object string."
            )

        # === UNKNOWN TYPE ===
        else:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Type conversion failed for '{param_name}': "
                        f"Unknown target type '{expected_type}'. "
                        f"Valid types: string, text, str, number, integer, int, float, "
                        f"boolean, bool, array, list, object, dict, json."
            )
        
        """
        # 1. String → Number
        self._convert_to_type("30", "number", "timeout")
        # Girdi: value="30", expected_type="number", param_name="timeout"
        # Çıktı: 30 (int)
        
        # 2. String → Float
        self._convert_to_type("30.5", "float", "price")
        # Girdi: value="30.5", expected_type="float", param_name="price"
        # Çıktı: 30.5 (float)
        
        # 3. String → Boolean
        self._convert_to_type("true", "boolean", "enabled")
        # Girdi: value="true", expected_type="boolean", param_name="enabled"
        # Çıktı: True (bool)
        
        self._convert_to_type("false", "boolean", "enabled")
        # Çıktı: False (bool)
        
        self._convert_to_type("1", "boolean", "enabled")
        # Çıktı: True (bool)
        
        # 4. String → Array (JSON)
        self._convert_to_type('[1, 2, 3]', "array", "items")
        # Girdi: value='[1, 2, 3]', expected_type="array", param_name="items"
        # Çıktı: [1, 2, 3] (list)
        
        # 5. String → Object (JSON)
        self._convert_to_type('{"key": "value"}', "object", "config")
        # Girdi: value='{"key": "value"}', expected_type="object", param_name="config"
        # Çıktı: {"key": "value"} (dict)
        
        # 6. Zaten doğru tipte ise direkt döndürür
        self._convert_to_type(30, "number", "timeout")
        # Girdi: value=30 (int), expected_type="number"
        # Çıktı: 30 (int) - dönüşüm yapmadan direkt döndürür
        
        # 7. None kontrolü
        self._convert_to_type(None, "string", "name")
        # Çıktı: None
        
        # 8. Hata durumu
        self._convert_to_type("abc", "number", "timeout")
        # InvalidInputError: Parameter 'timeout' cannot be converted to number
        """

    def _is_nested(self, path: str) -> bool:
        """
        Value'nın nested bir yapıda olup olmadığını kontrol eder.
        """
        if not isinstance(path, str):
            return False
        return "." in path or "[" in path

    def _resolve_nested_reference(self, data: Any, path: str) -> Any:
        """
        # Path'i parçalara ayır: key'ler ve array index'ler
        # Örnek: "user.email" → ["user", "email"]
        # Örnek: "items[0]" → ["items", "[0]"]
        # Örnek: "items[1].name" → ["items", "[1]", "name"]
        # Örnek: "user.details[0].name" → ["user", "details", "[0]", "name"]
        """
        if not path:
            return data
        
        if not isinstance(data, (dict, list)):
            raise InvalidInputError(
                message=f"Cannot resolve path '{path}' on non-nested data type: {type(data).__name__}"
            )
        
        parts = re.split(r'(\[.*?\])', path)  # Array index'leri ayır
        parts = [p for p in parts if p]  # Boş string'leri temizle
    
        final_parts = []
        for part in parts:
            if part.startswith("[") and part.endswith("]"):
                final_parts.append(part)
            else:
                keys = part.split(".")
                final_parts.extend(keys)
        final_parts = [p for p in final_parts if p]

        current_data = data
        for part in final_parts:
            if part.startswith("[") and part.endswith("]"):
                if not isinstance(current_data, list):
                    raise InvalidInputError(
                        message=f"Cannot access array index '{part}' on non-list data"
                    )
                try:
                    index = int(part[1:-1])
                    if index < 0 or index >= len(current_data):
                        raise InvalidInputError(
                            message=f"Array index '{index}' out of range (length: {len(current_data)})"
                        )
                    current_data = current_data[index]
                except ValueError:
                    raise InvalidInputError(
                        message=f"Invalid array index: {part}"
                    )
            else:
                if not isinstance(current_data, dict):
                    raise InvalidInputError(
                        message=f"Cannot access key '{part}' on non-dict data"
                    )
                if part not in current_data:
                    raise InvalidInputError(
                        message=f"Key '{part}' not found in data"
                    )
                current_data = current_data[part]
        return current_data

    def _get_static_data(self, reference_info: Dict[str, Any]) -> Any:
        value_str = reference_info["id"]
        expected_type = reference_info.get("expected_type", "string")
        param_name = reference_info.get("param_name")
        
        return self._convert_to_type(value_str, expected_type, param_name)

    def _get_trigger_data(
        self,
        session,
        reference_info: Dict[str, Any],
        execution_id: str
    ) -> Any:
        """
        Execution'dan trigger_data çek ve path ile resolve et.
        """
        path = reference_info.get("path")
        expected_type = reference_info.get("expected_type", "string")
        param_name = reference_info.get("param_name", "unknown")
        
        execution = self._execution_repo._get_by_id(session, record_id=execution_id, include_deleted=False)
        if not execution:
            raise ResourceNotFoundError(resource_name="execution", resource_id=execution_id)
        
        trigger_data = execution.trigger_data or {}
        
        if path:
            value = self._resolve_nested_reference(trigger_data, path)
        else:
            value = trigger_data
        
        return self._convert_to_type(value, expected_type, param_name)

    def _get_node_data(
        self,
        session,
        reference_info: Dict[str, Any],
        execution_id: str
    ) -> Any:
        """
        ExecutionOutput'tan node output çek ve path ile resolve et.
        """
        node_id = reference_info["id"]
        path = reference_info.get("path")
        expected_type = reference_info.get("expected_type", "string")
        param_name = reference_info.get("param_name", "unknown")
        
        execution_output = self._execution_output_repo._get_by_execution_and_node(
            session,
            execution_id=execution_id,
            node_id=node_id,
            include_deleted=False
        )
        
        if not execution_output:
            raise ResourceNotFoundError(resource_name="node_output", resource_id=node_id)
        
        result_data = execution_output.result_data or {}
        
        if path:
            value = self._resolve_nested_reference(result_data, path)
        else:
            value = result_data
        
        return self._convert_to_type(value, expected_type, param_name)
    
    def _get_value_data(
        self,
        session,
        reference_info: Dict[str, Any],
        workspace_id: str
    ) -> Any:
        """
        Variable reference'ını çöz.
        """
        variable_id = reference_info["id"]
        path = reference_info.get("path")
        expected_type = reference_info.get("expected_type", "string")
        param_name = reference_info.get("param_name", "unknown")
        
        variable = self._variable_repo._get_by_id(session, record_id=variable_id, include_deleted=False)
        if not variable:
            raise ResourceNotFoundError(resource_name="variable", resource_id=variable_id)
        
        if variable.workspace_id != workspace_id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Variable '{variable_id}' does not belong to workspace '{workspace_id}'"
            )
        
        if variable.is_secret:
            value = decrypt_data(variable.value)
        else:
            value = variable.value

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except:
                pass
        
        if path:
            value = self._resolve_nested_reference(value, path)
        
        return self._convert_to_type(value, expected_type, param_name)

    def _get_database_data(
        self,
        session,
        reference_info: Dict[str, Any],
        workspace_id: str
    ) -> Any:
        """
        Database reference'ını çöz.
        """
        database_id = reference_info["id"]
        path = reference_info.get("path")
        expected_type = reference_info.get("expected_type", "string")
        param_name = reference_info.get("param_name", "unknown")
        
        database = self._database_repo._get_by_id(session, record_id=database_id, include_deleted=False)
        if not database:
            raise ResourceNotFoundError(resource_name="database", resource_id=database_id)

        if database.workspace_id != workspace_id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Database '{database_id}' does not belong to workspace '{workspace_id}'"
            )

        data = {
            "connection_string": database.connection_string,
            "host": getattr(database, "host", None),
            "port": getattr(database, "port", None),
            "database_name": getattr(database, "database_name", None),
        }
        
        if path:
            value = self._resolve_nested_reference(data, path)
        else:
            value = data
        
        return self._convert_to_type(value, expected_type, param_name)

    def _get_file_data(
        self,
        session,
        reference_info: Dict[str, Any],
        workspace_id: str
    ) -> Any:
        """
        File reference'ını çöz.
        """
        file_id = reference_info["id"]
        path = reference_info.get("path", "content")
        expected_type = reference_info.get("expected_type", "string")
        param_name = reference_info.get("param_name", "unknown")
        
        file_obj = self._file_repo._get_by_id(session, record_id=file_id, include_deleted=False)
        if not file_obj:
            raise ResourceNotFoundError(resource_name="file", resource_id=file_id)
        
        if file_obj.workspace_id != workspace_id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"File '{file_id}' does not belong to workspace '{workspace_id}'"
            )
        
        if path == "content":
            file_path = get_workspace_file_path(workspace_id)
            full_path = os.path.join(file_path, file_obj.file_path)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    value = f.read()
            except Exception as e:
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Failed to read file content: {str(e)}"
                )
        elif path.startswith("metadata."):
            field = path.replace("metadata.", "")
            value = getattr(file_obj, field, None)
            if value is None:
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"File metadata field '{field}' not found"
                )
        else:
            value = getattr(file_obj, path, None)
            if value is None:
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"File field '{path}' not found"
                )
        
        return self._convert_to_type(value, expected_type, param_name)

    def _get_credential_data(
        self,
        session,
        reference_info: Dict[str, Any],
        workspace_id: str
    ) -> Any:
        """
        Credential reference'ını çöz.
        """
        credential_id = reference_info["id"]
        path = reference_info.get("path")
        expected_type = reference_info.get("expected_type")
        param_name = reference_info.get("param_name", "unknown")
        
        credential = self._credential_repo._get_by_id(session, record_id=credential_id, include_deleted=False)
        if not credential:
            raise ResourceNotFoundError(resource_name="credential", resource_id=credential_id)
        
        if credential.workspace_id != workspace_id:
            raise InvalidInputError(
                field_name=param_name,
                message=f"Credential '{credential_id}' does not belong to workspace '{workspace_id}'"
            )
        
        credential_data = decrypt_data(credential.credential_data)

        if path:
            value = self._resolve_nested_reference(credential_data, path)
        else:
            value = credential_data

        if expected_type:
            value = self._convert_to_type(value, expected_type, param_name)

        return value

    def update_next_node_dependencies(
        self,
        session,
        *,
        execution_id: str,
        completed_node_id: str
    ) -> int:
        """
        Bir node tamamlandığında sonraki node'ların dependency_count'unu azalt.
        previous_nodes ExecutionOutput'tan dinamik olarak sorgulanacak.
        """
        execution = self._execution_repo._get_by_id(session, record_id=execution_id, include_deleted=False)
        if not execution:
            raise ResourceNotFoundError(resource_name="execution", resource_id=execution_id)

        workflow_id = execution.workflow_id

        edges = self._edge_repo._get_by_from_node_id(
            session,
            workflow_id=workflow_id,
            from_node_id=completed_node_id,
            include_deleted=False
        )

        if not edges:
            return 0

        # Batch olarak tüm target node_id'leri topla
        target_node_ids = [edge.to_node_id for edge in edges]
        
        # Tüm execution input'ları tek sorguda getir
        all_execution_inputs = self._execution_input_repo._get_by_execution_id(
            session,
            record_id=execution_id,
            include_deleted=False
        )
        
        # node_id'ye göre map oluştur
        input_map = {inp.node_id: inp for inp in all_execution_inputs if inp.node_id in target_node_ids}

        updated_count = 0
        for edge in edges:
            target_input = input_map.get(edge.to_node_id)
            
            if target_input:
                if target_input.dependency_count > 0:
                    target_input.dependency_count -= 1
                    updated_count += 1

        return updated_count

    def resolve_references(
        self,
        session,
        groups: Dict[str, List[Dict[str, Any]]],
        execution_id: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """
        Gruplara ayrılmış reference'ları batch olarak resolve eder.
        
        Args:
            groups: resolve_parameters() tarafından oluşturulmuş reference grupları
            execution_id: Execution ID (trigger ve node data için gerekli)
            workspace_id: Workspace ID (value, credential, database, file için gerekli)
        
        Returns:
            {param_name: resolved_value} formatında resolve edilmiş parametreler
        """
        resolved_params = {}
        
        # Static'leri resolve et
        for ref_info in groups.get("static", []):
            value = self._get_static_data(ref_info)
            resolved_params[ref_info["param_name"]] = value
        
        # Trigger'ları resolve et (aynı execution_id için cache)
        trigger_data_cache = None
        for ref_info in groups.get("trigger", []):
            if trigger_data_cache is None:
                execution = self._execution_repo._get_by_id(session, record_id=execution_id, include_deleted=False)
                if not execution:
                    raise ResourceNotFoundError(resource_name="execution", resource_id=execution_id)
                trigger_data_cache = execution.trigger_data or {}
            
            path = ref_info.get("path")
            expected_type = ref_info.get("expected_type", "string")
            param_name = ref_info.get("param_name", "unknown")
            
            if path:
                value = self._resolve_nested_reference(trigger_data_cache, path)
            else:
                value = trigger_data_cache
            
            resolved_params[param_name] = self._convert_to_type(value, expected_type, param_name)
        
        # Node'ları resolve et (batch olarak)
        node_refs = groups.get("node", [])
        if node_refs:
            node_ids = list(set([ref_info["id"] for ref_info in node_refs if ref_info.get("id")]))
            node_outputs_map = {}
            
            if node_ids:
                all_outputs = self._execution_output_repo._get_by_execution_id(
                    session,
                    record_id=execution_id,
                    include_deleted=False
                )
                node_outputs_map = {out.node_id: out for out in all_outputs if out.node_id in node_ids}
            
            for ref_info in node_refs:
                node_id = ref_info["id"]
                path = ref_info.get("path")
                expected_type = ref_info.get("expected_type", "string")
                param_name = ref_info.get("param_name", "unknown")
                
                execution_output = node_outputs_map.get(node_id)
                if not execution_output:
                    raise ResourceNotFoundError(resource_name="node_output", resource_id=node_id)
                
                result_data = execution_output.result_data or {}
                if path:
                    value = self._resolve_nested_reference(result_data, path)
                else:
                    value = result_data
                
                resolved_params[param_name] = self._convert_to_type(value, expected_type, param_name)
        
        # Value'ları resolve et (batch olarak)
        value_refs = groups.get("value", [])
        if value_refs:
            variable_ids = list(set([ref_info["id"] for ref_info in value_refs if ref_info.get("id")]))
            variables_map = {}
            
            if variable_ids:
                variables = self._variable_repo._get_by_ids(session, record_ids=variable_ids, include_deleted=False)
                variables_map = {var.id: var for var in variables if var.workspace_id == workspace_id}
            
            for ref_info in value_refs:
                variable_id = ref_info["id"]
                path = ref_info.get("path")
                expected_type = ref_info.get("expected_type", "string")
                param_name = ref_info.get("param_name", "unknown")
                
                variable = variables_map.get(variable_id)
                if not variable:
                    raise ResourceNotFoundError(resource_name="variable", resource_id=variable_id)
                
                if variable.workspace_id != workspace_id:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Variable '{variable_id}' does not belong to workspace '{workspace_id}'"
                    )
                
                if variable.is_secret:
                    value = decrypt_data(variable.value)
                else:
                    value = variable.value
                
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                
                if path:
                    value = self._resolve_nested_reference(value, path)
                
                resolved_params[param_name] = self._convert_to_type(value, expected_type, param_name)
        
        # Credential'ları resolve et (batch olarak)
        credential_refs = groups.get("credential", [])
        if credential_refs:
            credential_ids = list(set([ref_info["id"] for ref_info in credential_refs if ref_info.get("id")]))
            credentials_map = {}
            
            if credential_ids:
                credentials = self._credential_repo._get_by_ids(session, record_ids=credential_ids, include_deleted=False)
                credentials_map = {cred.id: cred for cred in credentials if cred.workspace_id == workspace_id}
            
            for ref_info in credential_refs:
                credential_id = ref_info["id"]
                path = ref_info.get("path")
                expected_type = ref_info.get("expected_type")
                param_name = ref_info.get("param_name", "unknown")
                
                credential = credentials_map.get(credential_id)
                if not credential:
                    raise ResourceNotFoundError(resource_name="credential", resource_id=credential_id)
                
                if credential.workspace_id != workspace_id:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Credential '{credential_id}' does not belong to workspace '{workspace_id}'"
                    )
                
                credential_data = decrypt_data(credential.credential_data)
                if path:
                    value = self._resolve_nested_reference(credential_data, path)
                else:
                    value = credential_data
                
                if expected_type:
                    value = self._convert_to_type(value, expected_type, param_name)
                
                resolved_params[param_name] = value
        
        # Database'leri resolve et (batch olarak)
        database_refs = groups.get("database", [])
        if database_refs:
            database_ids = list(set([ref_info["id"] for ref_info in database_refs if ref_info.get("id")]))
            databases_map = {}
            
            if database_ids:
                databases = self._database_repo._get_by_ids(session, record_ids=database_ids, include_deleted=False)
                databases_map = {db.id: db for db in databases if db.workspace_id == workspace_id}
            
            for ref_info in database_refs:
                database_id = ref_info["id"]
                path = ref_info.get("path")
                expected_type = ref_info.get("expected_type", "string")
                param_name = ref_info.get("param_name", "unknown")
                
                database = databases_map.get(database_id)
                if not database:
                    raise ResourceNotFoundError(resource_name="database", resource_id=database_id)
                
                if database.workspace_id != workspace_id:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Database '{database_id}' does not belong to workspace '{workspace_id}'"
                    )
                
                data = {
                    "connection_string": database.connection_string,
                    "host": getattr(database, "host", None),
                    "port": getattr(database, "port", None),
                    "database_name": getattr(database, "database_name", None),
                }
                
                if path:
                    value = self._resolve_nested_reference(data, path)
                else:
                    value = data
                
                resolved_params[param_name] = self._convert_to_type(value, expected_type, param_name)
        
        # File'ları resolve et (batch olarak)
        file_refs = groups.get("file", [])
        if file_refs:
            file_ids = list(set([ref_info["id"] for ref_info in file_refs if ref_info.get("id")]))
            files_map = {}
            
            if file_ids:
                files = self._file_repo._get_by_ids(session, record_ids=file_ids, include_deleted=False)
                files_map = {f.id: f for f in files if f.workspace_id == workspace_id}
            
            for ref_info in file_refs:
                file_id = ref_info["id"]
                path = ref_info.get("path", "content")
                expected_type = ref_info.get("expected_type", "string")
                param_name = ref_info.get("param_name", "unknown")
                
                file_obj = files_map.get(file_id)
                if not file_obj:
                    raise ResourceNotFoundError(resource_name="file", resource_id=file_id)
                
                if file_obj.workspace_id != workspace_id:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"File '{file_id}' does not belong to workspace '{workspace_id}'"
                    )
                
                if path == "content":
                    file_path = get_workspace_file_path(workspace_id)
                    full_path = os.path.join(file_path, file_obj.file_path)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            value = f.read()
                    except Exception as e:
                        raise InvalidInputError(
                            field_name=param_name,
                            message=f"Failed to read file content: {str(e)}"
                        )
                elif path.startswith("metadata."):
                    field = path.replace("metadata.", "")
                    value = getattr(file_obj, field, None)
                    if value is None:
                        raise InvalidInputError(
                            field_name=param_name,
                            message=f"File metadata field '{field}' not found"
                        )
                else:
                    value = getattr(file_obj, path, None)
                    if value is None:
                        raise InvalidInputError(
                            field_name=param_name,
                            message=f"File field '{path}' not found"
                        )
                
                resolved_params[param_name] = self._convert_to_type(value, expected_type, param_name)
        
        return resolved_params

    @with_readonly_session(manager=None)
    def process_task_context(
        self,
        session,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        InputHandler tarafından çağrılan metod.
        Task'tan execution context oluşturur.
        
        Args:
            task: InputHandler'dan gelen task dict
                {
                    "id": "EXI-...",  # execution_input_id
                    "node_name": "...",
                    "script_path": "...",
                    ...
                }
        
        Returns:
            Execution context dict (create_execution_context ile aynı format)
        """
        execution_input_id = task.get("id")
        if not execution_input_id:
            raise InvalidInputError(
                message="Task must contain 'id' field (execution_input_id)"
            )
        
        return self.create_execution_context(session, execution_input_id=execution_input_id)

    @with_readonly_session(manager=None)
    def create_execution_context(
        self,
        session,
        execution_input_id: str
    ) -> Dict[str, Any]:
        """
        ExecutionInput'tan execution context oluşturur.
        
        Adımlar:
        1. ExecutionInput'u getir
        2. params'taki reference'ları resolve et (trigger, node, value, credential, database, file)
        3. Previous nodes'ları ExecutionOutput'tan sorgula
        4. Trigger data'yı Execution'dan al
        5. Script parametrelerini flat yapıda hazırla
        
        Args:
            execution_input_id: ExecutionInput ID
        
        Returns:
            {
                "script_path": "...",
                "script_name": "...",
                "params": {...},  # Flat yapıda resolve edilmiş script parametreleri
                "execution_id": "...",  # Takip için
                "node_id": "...",  # Takip için
                "max_retries": 3,
                "timeout_seconds": 300
            }
        """
        execution_input = self._execution_input_repo._get_by_id(
            session,
            record_id=execution_input_id,
            include_deleted=False
        )
        if not execution_input:
            raise ResourceNotFoundError(
                resource_name="execution_input",
                resource_id=execution_input_id
            )
        
        execution_id = execution_input.execution_id
        workspace_id = execution_input.workspace_id
        node_id = execution_input.node_id
        params = execution_input.params or {}
        
        # Reference'ları gruplara ayır
        groups = self.resolve_parameters(params)
        
        # Reference'ları resolve et (trigger, node, value, credential, database, file)
        resolved_params = self.resolve_references(
            session,
            groups=groups,
            execution_id=execution_id,
            workspace_id=workspace_id
        )
        
        # Resolve edilmemiş parametreleri de ekle (reference olmayanlar)
        for param_name, param_data in params.items():
            if param_name not in resolved_params:
                value = param_data.get("value")
                if not (isinstance(value, str) and self._is_reference(value)):
                    resolved_params[param_name] = value
        
        # Previous nodes ve trigger data resolve_references içinde zaten işleniyor
        # Node reference'ları (${node:...}) ExecutionOutput'tan sorgulanıyor
        # Trigger reference'ları (${trigger:...}) Execution'dan sorgulanıyor
        # resolved_params zaten flat yapıda script parametrelerini içeriyor
        
        return {
            "script_path": execution_input.script_path,
            "script_name": execution_input.script_name,
            "params": resolved_params,  # Flat yapıda script parametreleri
            "execution_id": execution_id,  # Takip için
            "node_id": node_id,  # Takip için
            "max_retries": execution_input.max_retries,
            "timeout_seconds": execution_input.timeout_seconds
        }

    @with_transaction(manager=None)
    def process_execution_result(
        self,
        session,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Engine'den gelen execution result'ı işler.
        
        Adımlar:
        1. ExecutionOutput oluştur
        2. Node başarılıysa → update_next_node_dependencies çağır
        3. Tüm input'lar bittiyse → execution'ı tamamla
        
        Not: ExecutionInput'lar engine'e gönderildiği anda silinir (InputHandler'da)
        
        Args:
            result: Engine'den gelen result
                {
                    "execution_id": "...",
                    "node_id": "...",
                    "status": "SUCCESS" | "FAILED",
                    "result_data": {...},
                    "stdout": "...",
                    "stderr": "...",
                    "duration": 123.45,
                    "memory_mb": 256.0,
                    "cpu_percent": 50.0,
                    "error_message": "...",
                    "error_details": {...}
                }
        
        Returns:
            {
                "execution_output_id": "...",
                "updated_dependencies": 0,
                "execution_completed": False
            }
        """
        execution_id = result.get("execution_id")
        node_id = result.get("node_id")
        status_str = result.get("status", "FAILED")
        
        if not execution_id or not node_id:
            raise InvalidInputError(
                message="execution_id and node_id are required in result"
            )
        
        # Execution'ı kontrol et ve workflow_id, workspace_id'yi al
        execution = self._execution_repo._get_by_id(
            session,
            record_id=execution_id,
            include_deleted=False
        )
        if not execution:
            raise ResourceNotFoundError(
                resource_name="execution",
                resource_id=execution_id
            )
        
        workflow_id = execution.workflow_id
        workspace_id = execution.workspace_id
        
        # Status'u string'e çevir (ExecutionOutput modeli string bekliyor)
        status_map = {
            "SUCCESS": "COMPLETED",
            "FAILED": "FAILED",
            "TIMEOUT": "TIMEOUT",
            "CANCELLED": "CANCELLED",
        }
        status_str_final = status_map.get(status_str.upper(), "FAILED")
        
        # ExecutionOutput oluştur
        execution_output = self._execution_output_repo._create(
            session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            node_id=node_id,
            status=status_str_final,
            result_data=result.get("result_data", {}),
            started_at=result.get("started_at"),
            ended_at=result.get("ended_at") or datetime.now(timezone.utc),
            memory_mb=result.get("memory_mb"),
            cpu_percent=result.get("cpu_percent"),
            error_message=result.get("error_message"),
            error_details=result.get("error_details", {}),
            retry_count=result.get("retry_count", 0)
        )
        
        # Node başarılıysa dependency'leri güncelle
        updated_dependencies = 0
        if status_str_final == "COMPLETED":
            updated_dependencies = self.update_next_node_dependencies(
                session,
                execution_id=execution_id,
                completed_node_id=node_id
            )
        
        # Execution'ın tamamlanıp tamamlanmadığını kontrol et
        # ExecutionInput'lar engine'e gönderildiği anda silindiği için
        # Workflow'daki node sayısı ile ExecutionOutput sayısını karşılaştır
        
        # Workflow'daki node sayısını al
        workflow = self._workflow_repo._get_by_id(
            session,
            record_id=workflow_id,
            include_deleted=False
        )
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="workflow",
                resource_id=workflow_id
            )
        
        # Workflow'daki node sayısı
        workflow_node_count = len(workflow.nodes) if workflow.nodes else 0
        
        # ExecutionOutput sayısı
        outputs = self._execution_output_repo._get_by_execution_id(
            session,
            record_id=execution_id,
            include_deleted=False
        )
        output_count = len(outputs)
        
        # Tüm node'lar için output varsa execution tamamlanmış demektir
        execution_completed = workflow_node_count > 0 and output_count >= workflow_node_count
        
        # Eğer node FAILED ise veya execution tamamlandıysa end_execution çağır
        should_end_execution = False
        final_status = None
        
        if status_str_final == "FAILED":
            # Node FAILED ise execution'ı FAILED olarak sonlandır
            should_end_execution = True
            final_status = ExecutionStatus.FAILED
        elif execution_completed:
            # Son düğüm tamamlandıysa execution'ı tamamla
            should_end_execution = True
            # Output'larda FAILED var mı kontrol et
            has_failed = any(output.status == "FAILED" for output in outputs)
            final_status = ExecutionStatus.FAILED if has_failed else ExecutionStatus.COMPLETED
        
        if should_end_execution:
            # ExecutionService._end_execution çağır (mevcut transaction içinde)
            from src.miniflow.services.execution_services.execution_service import ExecutionService
            execution_service = ExecutionService()
            execution_service._registry._db_manager = self._registry._db_manager  # Aynı DB manager'ı kullan
            execution_service._end_execution(
                session,
                execution_id=execution_id,
                status=final_status
            )
        
        return {
            "execution_output_id": execution_output.id,
            "updated_dependencies": updated_dependencies,
            "execution_completed": should_end_execution
        }

    @with_transaction(manager=None)
    def remove_processed_execution_inputs(
        self,
        session,
        execution_input_ids: List[str]
    ) -> int:
        """
        İşlenmiş execution input'ları soft delete yapar.
        InputHandler tarafından engine'e gönderildikten sonra çağrılır.
        
        Args:
            execution_input_ids: Soft delete yapılacak execution input ID'leri
        
        Returns:
            Silinen input sayısı
        """
        if not execution_input_ids:
            return 0
        
        # Batch olarak tüm input'ları getir
        execution_inputs = self._execution_input_repo._get_by_ids(
            session,
            record_ids=execution_input_ids,
            include_deleted=False
        )
        
        # Soft delete yap
        now = datetime.now(timezone.utc)
        deleted_count = 0
        for execution_input in execution_inputs:
            if not execution_input.is_deleted:
                execution_input.is_deleted = True
                execution_input.deleted_at = now
                deleted_count += 1
        
        return deleted_count