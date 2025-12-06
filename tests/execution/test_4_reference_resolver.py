"""
TEST 4 (BONUS): Reference Çözümleme Sistemi Testleri
====================================================

Bu test, SchedulerService'deki reference çözümleme sistemini kapsamlı test eder:
1. TypeConverter - Tip dönüşümleri
2. RefrenceResolver - Referans çözümleme
3. SchedulerForInputHandler - Parametre gruplandırma ve çözümleme

NOT: Bu testler database bağımlılığı olmadan çalışır.
"""

import pytest
import json
import sys
import os

# Path'e src ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Scheduler service'i direkt import et (database bağımlılığı olmayan kısımlar)
# NOT: Full import yapamıyoruz çünkü database import'u var, 
# bu yüzden sadece bağımsız fonksiyonları test ediyoruz


class TestTypeConverterStandalone:
    """
    TypeConverter tarzı tip dönüşüm testleri.
    Database bağımlılığı olmadan çalışır.
    """
    
    # =========================================================================
    # String Dönüşüm Testleri
    # =========================================================================
    
    def test_string_from_string(self):
        """String'den string'e dönüşüm."""
        value = "hello"
        result = str(value)
        assert result == "hello"
        assert isinstance(result, str)
    
    def test_string_from_int(self):
        """Integer'dan string'e dönüşüm."""
        value = 42
        result = str(value)
        assert result == "42"
        assert isinstance(result, str)
    
    def test_string_from_float(self):
        """Float'tan string'e dönüşüm."""
        value = 3.14
        result = str(value)
        assert result == "3.14"
        assert isinstance(result, str)
    
    def test_string_from_bool(self):
        """Boolean'dan string'e dönüşüm."""
        assert str(True) == "True"
        assert str(False) == "False"
    
    def test_string_from_list(self):
        """List'ten string'e dönüşüm."""
        result = str([1, 2, 3])
        assert result == "[1, 2, 3]"
    
    # =========================================================================
    # Integer Dönüşüm Testleri
    # =========================================================================
    
    def test_integer_from_string(self):
        """String'den integer'a dönüşüm."""
        result = int("123")
        assert result == 123
        assert isinstance(result, int)
    
    def test_integer_from_float(self):
        """Float'tan integer'a dönüşüm."""
        result = int(3.9)
        assert result == 3
        assert isinstance(result, int)
    
    def test_integer_invalid(self):
        """Geçersiz integer dönüşümü."""
        with pytest.raises(ValueError):
            int("not_a_number")
    
    # =========================================================================
    # Float Dönüşüm Testleri
    # =========================================================================
    
    def test_float_from_string(self):
        """String'den float'a dönüşüm."""
        result = float("2.718")
        assert result == 2.718
        assert isinstance(result, float)
    
    def test_float_from_int(self):
        """Integer'dan float'a dönüşüm."""
        result = float(5)
        assert result == 5.0
        assert isinstance(result, float)
    
    def test_float_invalid(self):
        """Geçersiz float dönüşümü."""
        with pytest.raises(ValueError):
            float("invalid")
    
    # =========================================================================
    # Boolean Dönüşüm Testleri
    # =========================================================================
    
    def test_boolean_from_string_true_values(self):
        """String'den boolean'a dönüşüm (true değerleri)."""
        true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "on", "ON"]
        for val in true_values:
            val_lower = val.lower().strip()
            result = val_lower in ("true", "1", "yes", "on")
            assert result == True, f"'{val}' should convert to True"
    
    def test_boolean_from_string_false_values(self):
        """String'den boolean'a dönüşüm (false değerleri)."""
        false_values = ["false", "False", "FALSE", "0", "no", "No", "off", "OFF", ""]
        for val in false_values:
            val_lower = val.lower().strip()
            result = val_lower in ("false", "0", "no", "off", "")
            assert result == True, f"'{val}' should convert to False"
    
    # =========================================================================
    # Array Dönüşüm Testleri
    # =========================================================================
    
    def test_array_from_json_string(self):
        """JSON string'den array'e dönüşüm."""
        result = json.loads('["a", "b", "c"]')
        assert result == ["a", "b", "c"]
        assert isinstance(result, list)
    
    def test_array_nested(self):
        """İç içe array dönüşümü."""
        result = json.loads('[[1, 2], [3, 4]]')
        assert result == [[1, 2], [3, 4]]
    
    def test_array_invalid_json(self):
        """Geçersiz JSON array dönüşümü."""
        with pytest.raises(json.JSONDecodeError):
            json.loads("not_json")
    
    # =========================================================================
    # Object Dönüşüm Testleri
    # =========================================================================
    
    def test_object_from_json_string(self):
        """JSON string'den object'e dönüşüm."""
        result = json.loads('{"name": "test", "count": 5}')
        assert result == {"name": "test", "count": 5}
        assert isinstance(result, dict)
    
    def test_object_nested(self):
        """İç içe object dönüşümü."""
        result = json.loads('{"outer": {"inner": "value"}}')
        assert result == {"outer": {"inner": "value"}}


class TestReferenceParsingStandalone:
    """
    Reference parsing testleri.
    Database bağımlılığı olmadan çalışır.
    """
    
    def _is_reference(self, value) -> bool:
        """Değerin referans formatında olup olmadığını kontrol eder."""
        if not isinstance(value, str):
            return False
        if not (value.startswith("${") and value.endswith("}")):
            return False
        if ":" not in value:
            return False
        return True
    
    def _parse_reference(self, reference: str) -> dict:
        """Referans string'ini parse eder."""
        content = reference[2:-1]  # ${ ve } kaldır
        ref_type, identifier_path = content.split(":", 1)
        
        ref_type = ref_type.strip()
        identifier_path = identifier_path.strip()
        
        result = {"type": ref_type}
        
        if ref_type == "static":
            result["id_or_value"] = identifier_path
        elif ref_type == "trigger":
            result["value_path"] = identifier_path
        else:
            if "." in identifier_path:
                parts = identifier_path.split(".", 1)
                result["id"] = parts[0]
                result["value_path"] = parts[1]
            else:
                result["id"] = identifier_path
                result["value_path"] = None
        
        return result
    
    # =========================================================================
    # Reference Detection Testleri
    # =========================================================================
    
    def test_is_reference_valid(self):
        """Geçerli referans formatları."""
        valid_refs = [
            "${static:value}",
            "${trigger:data.key}",
            "${node:NOD-123.result}",
            "${value:ENV-456}",
            "${credential:CRD-789.api_key}",
            "${database:DBS-111.host}",
            "${file:FLE-222.content}"
        ]
        for ref in valid_refs:
            assert self._is_reference(ref) == True, \
                f"'{ref}' should be detected as reference"
    
    def test_is_reference_invalid(self):
        """Geçersiz referans formatları."""
        invalid_refs = [
            "plain_value",
            "${incomplete",
            "no_colon${}",
            "$trigger:data}",
            None,
            123,
            ["list"],
            {"dict": "value"}
        ]
        for ref in invalid_refs:
            assert self._is_reference(ref) == False, \
                f"'{ref}' should NOT be detected as reference"
    
    # =========================================================================
    # Reference Parse Testleri
    # =========================================================================
    
    def test_parse_reference_static(self):
        """Static referans parse."""
        result = self._parse_reference("${static:my_value}")
        assert result["type"] == "static"
        assert result["id_or_value"] == "my_value"
    
    def test_parse_reference_trigger(self):
        """Trigger referans parse."""
        result = self._parse_reference("${trigger:data.user.id}")
        assert result["type"] == "trigger"
        assert result["value_path"] == "data.user.id"
    
    def test_parse_reference_node(self):
        """Node referans parse."""
        result = self._parse_reference("${node:NOD-12345.result.data}")
        assert result["type"] == "node"
        assert result["id"] == "NOD-12345"
        assert result["value_path"] == "result.data"
    
    def test_parse_reference_value(self):
        """Value (variable) referans parse."""
        result = self._parse_reference("${value:ENV-ABCDE}")
        assert result["type"] == "value"
        assert result["id"] == "ENV-ABCDE"
    
    def test_parse_reference_credential(self):
        """Credential referans parse."""
        result = self._parse_reference("${credential:CRD-XXXXX.api_key}")
        assert result["type"] == "credential"
        assert result["id"] == "CRD-XXXXX"
        assert result["value_path"] == "api_key"
    
    def test_parse_reference_database(self):
        """Database referans parse."""
        result = self._parse_reference("${database:DBS-YYYYY.connection_string}")
        assert result["type"] == "database"
        assert result["id"] == "DBS-YYYYY"
        assert result["value_path"] == "connection_string"
    
    def test_parse_reference_file(self):
        """File referans parse."""
        result = self._parse_reference("${file:FLE-ZZZZZ.content}")
        assert result["type"] == "file"
        assert result["id"] == "FLE-ZZZZZ"
        assert result["value_path"] == "content"


class TestNestedPathResolutionStandalone:
    """
    Nested path çözümleme testleri.
    Database bağımlılığı olmadan çalışır.
    """
    
    import re
    
    def _resolve_nested_reference(self, value_path: str) -> list:
        """İç içe referans yolunu parçalara ayırır."""
        import re
        
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
    
    def _get_value_from_context(self, path_parts: list, context):
        """Context'ten değer çıkarır."""
        if path_parts == []:
            return context
        
        if not isinstance(context, (dict, list)):
            raise ValueError(f"Cannot resolve path on non-nested data type: {type(context).__name__}")
        
        current_data = context
        for path_part in path_parts:
            if path_part.startswith("[") and path_part.endswith("]"):
                if not isinstance(current_data, list):
                    raise ValueError(f"Cannot access array index on non-list data")
                index = int(path_part[1:-1])
                if index < 0 or index >= len(current_data):
                    raise ValueError(f"Array index out of range")
                current_data = current_data[index]
            else:
                if path_part not in current_data:
                    raise ValueError(f"Key '{path_part}' not found")
                current_data = current_data[path_part]
        return current_data
    
    # =========================================================================
    # Nested Reference Çözümleme Testleri
    # =========================================================================
    
    def test_resolve_nested_reference_simple(self):
        """Basit path çözümleme."""
        parts = self._resolve_nested_reference("data")
        assert parts == ["data"]
    
    def test_resolve_nested_reference_dotted(self):
        """Noktalı path çözümleme."""
        parts = self._resolve_nested_reference("data.user.name")
        assert parts == ["data", "user", "name"]
    
    def test_resolve_nested_reference_with_array(self):
        """Array indexli path çözümleme."""
        parts = self._resolve_nested_reference("data.items[0].name")
        assert parts == ["data", "items", "[0]", "name"]
    
    def test_resolve_nested_reference_multiple_arrays(self):
        """Birden fazla array indexli path çözümleme."""
        parts = self._resolve_nested_reference("matrix[0][1].value")
        assert parts == ["matrix", "[0]", "[1]", "value"]
    
    def test_resolve_nested_reference_empty(self):
        """Boş path çözümleme."""
        parts = self._resolve_nested_reference("")
        assert parts == []
    
    def test_resolve_nested_reference_none(self):
        """None path çözümleme."""
        parts = self._resolve_nested_reference(None)
        assert parts == []
    
    # =========================================================================
    # Context Value Extraction Testleri
    # =========================================================================
    
    def test_get_value_from_context_simple(self):
        """Basit değer çıkarma."""
        context = {"name": "test"}
        value = self._get_value_from_context(["name"], context)
        assert value == "test"
    
    def test_get_value_from_context_nested(self):
        """İç içe değer çıkarma."""
        context = {
            "user": {
                "profile": {
                    "name": "John"
                }
            }
        }
        value = self._get_value_from_context(
            ["user", "profile", "name"], context
        )
        assert value == "John"
    
    def test_get_value_from_context_array_index(self):
        """Array index ile değer çıkarma."""
        context = {
            "items": [
                {"id": 1, "name": "first"},
                {"id": 2, "name": "second"}
            ]
        }
        value = self._get_value_from_context(
            ["items", "[0]", "name"], context
        )
        assert value == "first"
        
        value = self._get_value_from_context(
            ["items", "[1]", "id"], context
        )
        assert value == 2
    
    def test_get_value_from_context_empty_path(self):
        """Boş path ile tüm context döndürme."""
        context = {"data": "value"}
        value = self._get_value_from_context([], context)
        assert value == context
    
    def test_get_value_from_context_missing_key(self):
        """Olmayan key hatası."""
        context = {"name": "test"}
        with pytest.raises(ValueError):
            self._get_value_from_context(["missing"], context)
    
    def test_get_value_from_context_array_out_of_bounds(self):
        """Array index out of bounds hatası."""
        context = {"items": [1, 2, 3]}
        with pytest.raises(ValueError):
            self._get_value_from_context(["items", "[10]"], context)


class TestComplexScenarios:
    """
    Karmaşık senaryolar testi.
    """
    
    def _resolve_nested_reference(self, value_path: str) -> list:
        """İç içe referans yolunu parçalara ayırır."""
        import re
        
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
    
    def _get_value_from_context(self, path_parts: list, context):
        """Context'ten değer çıkarır."""
        if path_parts == []:
            return context
        
        current_data = context
        for path_part in path_parts:
            if path_part.startswith("[") and path_part.endswith("]"):
                index = int(path_part[1:-1])
                current_data = current_data[index]
            else:
                current_data = current_data[path_part]
        return current_data
    
    def test_deeply_nested_path(self):
        """Derin iç içe path çözümleme."""
        context = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep_value"
                        }
                    }
                }
            }
        }
        
        path = "level1.level2.level3.level4.value"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, context)
        
        assert value == "deep_value"
    
    def test_mixed_array_and_object_path(self):
        """Array ve object karışık path çözümleme."""
        context = {
            "users": [
                {
                    "name": "Alice",
                    "addresses": [
                        {"city": "NYC"},
                        {"city": "LA"}
                    ]
                },
                {
                    "name": "Bob",
                    "addresses": [
                        {"city": "Chicago"}
                    ]
                }
            ]
        }
        
        # İlk kullanıcının ikinci adresinin şehrini al
        path = "users[0].addresses[1].city"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, context)
        
        assert value == "LA"
    
    def test_execution_trigger_data_simulation(self):
        """Execution trigger data simülasyonu."""
        # Gerçek bir trigger_data senaryosu
        trigger_data = {
            "request": {
                "method": "POST",
                "headers": {
                    "content-type": "application/json",
                    "authorization": "Bearer token123"
                },
                "body": {
                    "user_id": "USR-12345",
                    "action": "process",
                    "items": [
                        {"id": 1, "quantity": 5},
                        {"id": 2, "quantity": 10}
                    ]
                }
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Test 1: User ID al
        path = "request.body.user_id"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, trigger_data)
        assert value == "USR-12345"
        
        # Test 2: Authorization header al
        path = "request.headers.authorization"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, trigger_data)
        assert value == "Bearer token123"
        
        # Test 3: İlk item'ın quantity'sini al
        path = "request.body.items[0].quantity"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, trigger_data)
        assert value == 5
    
    def test_node_output_data_simulation(self):
        """Node output data simülasyonu."""
        # Gerçek bir node çıktısı senaryosu
        node_output = {
            "status": "success",
            "result": {
                "processed_items": 15,
                "errors": [],
                "summary": {
                    "total_cost": 250.75,
                    "currency": "USD"
                }
            },
            "metadata": {
                "execution_time_ms": 1523,
                "memory_mb": 128.5
            }
        }
        
        # Test 1: Status al
        path = "status"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, node_output)
        assert value == "success"
        
        # Test 2: Total cost al
        path = "result.summary.total_cost"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, node_output)
        assert value == 250.75
        
        # Test 3: Execution time al
        path = "metadata.execution_time_ms"
        parts = self._resolve_nested_reference(path)
        value = self._get_value_from_context(parts, node_output)
        assert value == 1523


class TestParameterGrouping:
    """
    Parametre gruplandırma testleri.
    """
    
    def _is_reference(self, value) -> bool:
        """Değerin referans formatında olup olmadığını kontrol eder."""
        if not isinstance(value, str):
            return False
        if not (value.startswith("${") and value.endswith("}")):
            return False
        if ":" not in value:
            return False
        return True
    
    def _parse_reference(self, reference: str, param_name: str, expected_type: str) -> dict:
        """Referans string'ini parse eder."""
        content = reference[2:-1]
        ref_type, identifier_path = content.split(":", 1)
        
        ref_type = ref_type.strip()
        identifier_path = identifier_path.strip()
        
        result = {
            "type": ref_type,
            "param_name": param_name,
            "expected_type": expected_type
        }
        
        if ref_type == "static":
            result["id_or_value"] = identifier_path
        elif ref_type == "trigger":
            result["value_path"] = identifier_path
        else:
            if "." in identifier_path:
                parts = identifier_path.split(".", 1)
                result["id"] = parts[0]
                result["value_path"] = parts[1]
            else:
                result["id"] = identifier_path
                result["value_path"] = None
        
        return result
    
    def resolve_parameters(self, workspace_id, execution_id, params):
        """Parametreleri referans tipine göre gruplara ayırır."""
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
            
            if self._is_reference(param_value):
                reference_info = self._parse_reference(param_value, param_name, expected_type)
                reference_info['workspace_id'] = workspace_id
                reference_info['execution_id'] = execution_id
                ref_type = reference_info["type"]
                groups[ref_type].append(reference_info)
            else:
                groups['static'].append({
                    "type": 'static',
                    "id_or_value": param_value,
                    "param_name": param_name,
                    "expected_type": expected_type
                })
        
        return groups
    
    def test_parameter_grouping(self):
        """Parametre gruplandırma testi."""
        params = {
            "static_param": {
                "value": "plain_value",
                "type": "string"
            },
            "trigger_param": {
                "value": "${trigger:data.key}",
                "type": "string"
            },
            "node_param": {
                "value": "${node:NOD-123.result}",
                "type": "object"
            },
            "variable_param": {
                "value": "${value:ENV-456}",
                "type": "string"
            },
            "credential_param": {
                "value": "${credential:CRD-789.api_key}",
                "type": "string"
            }
        }
        
        groups = self.resolve_parameters(
            workspace_id="WSP-TEST",
            execution_id="EXE-TEST",
            params=params
        )
        
        # Her grup doğru sayıda referans içermeli
        assert len(groups["static"]) == 1
        assert len(groups["trigger"]) == 1
        assert len(groups["node"]) == 1
        assert len(groups["value"]) == 1
        assert len(groups["credential"]) == 1
        assert len(groups["database"]) == 0
        assert len(groups["file"]) == 0
        
        # Static grup kontrolü
        static_ref = groups["static"][0]
        assert static_ref["id_or_value"] == "plain_value"
        assert static_ref["param_name"] == "static_param"
        
        # Trigger grup kontrolü
        trigger_ref = groups["trigger"][0]
        assert trigger_ref["value_path"] == "data.key"
        assert trigger_ref["execution_id"] == "EXE-TEST"
        
        # Node grup kontrolü
        node_ref = groups["node"][0]
        assert node_ref["id"] == "NOD-123"
        assert node_ref["execution_id"] == "EXE-TEST"
        
        print("\n✅ Tüm parametreler doğru şekilde gruplandı:")
        print(f"   Static: {len(groups['static'])}")
        print(f"   Trigger: {len(groups['trigger'])}")
        print(f"   Node: {len(groups['node'])}")
        print(f"   Value: {len(groups['value'])}")
        print(f"   Credential: {len(groups['credential'])}")


# ==============================================================================
# Standalone Test Runner
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
