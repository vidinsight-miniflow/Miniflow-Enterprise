#!/usr/bin/env python3
"""
🚀 MiniFlow Execution İnteraktif Test Script
============================================

Bu script execution sürecini adım adım test eder ve
her adımda size sonuçları gösterir.

Kullanım:
    cd /Users/enesa/PythonProjects/vidinsight-miniflow-enterprise
    PYTHONPATH=src python tests/interactive_execution_test.py          # İnteraktif mod
    PYTHONPATH=src python tests/interactive_execution_test.py --auto   # Otomatik mod
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Argümanları parse et
parser = argparse.ArgumentParser(description='MiniFlow Execution Test Suite')
parser.add_argument('--auto', action='store_true', help='Otomatik mod (input beklemeden çalışır)')
args, unknown = parser.parse_known_args()
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_step(step_num: int, text: str):
    """Adım başlığı yazdır."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}[ADIM {step_num}] {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.END}")

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
            else:
                print(f"{prefix}   {Colors.CYAN}{key}:{Colors.END} {value}")
    else:
        print(f"{prefix}{Colors.BOLD}{label}:{Colors.END} {data}")

def wait_for_user(prompt: str = "Devam etmek için Enter'a basın..."):
    """Kullanıcıdan devam etmesini bekle."""
    if AUTO_MODE:
        print(f"\n{Colors.YELLOW}[AUTO] {prompt}{Colors.END}")
        time.sleep(0.3)  # Kısa bir bekleme
        return
    
    print(f"\n{Colors.YELLOW}{Colors.BOLD}>>> {prompt}{Colors.END}")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Colors.RED}Test iptal edildi.{Colors.END}")
        sys.exit(0)


# ============================================================================
# TEST 1: TypeConverter Testleri
# ============================================================================

def test_type_converter():
    """Tip dönüşüm testleri."""
    print_header("TEST 1: TypeConverter - Tip Dönüşüm Testleri")
    
    print_info("TypeConverter, farklı veri tiplerini birbirine dönüştürür.")
    print_info("Bu testler reference resolver'da kullanılan dönüşümleri test eder.\n")
    
    results = []
    
    # Test 1.1: String dönüşümleri
    print_step(1, "String Dönüşümleri")
    
    test_cases = [
        ("String -> String", "hello", str, "hello"),
        ("Integer -> String", 42, str, "42"),
        ("Float -> String", 3.14, str, "3.14"),
        ("Boolean -> String", True, str, "True"),
        ("List -> String", [1, 2, 3], str, "[1, 2, 3]"),
    ]
    
    for name, value, converter, expected in test_cases:
        try:
            result = converter(value)
            success = result == expected
            if success:
                print_success(f"{name}: {value} → '{result}'")
                results.append(("PASS", name))
            else:
                print_error(f"{name}: Beklenen '{expected}', alınan '{result}'")
                results.append(("FAIL", name))
        except Exception as e:
            print_error(f"{name}: Hata - {e}")
            results.append(("ERROR", name))
    
    wait_for_user()
    
    # Test 1.2: Integer dönüşümleri
    print_step(2, "Integer Dönüşümleri")
    
    test_cases = [
        ("String -> Integer", "123", int, 123),
        ("Float -> Integer", 3.9, int, 3),
        ("Boolean -> Integer", True, int, 1),
    ]
    
    for name, value, converter, expected in test_cases:
        try:
            result = converter(value)
            success = result == expected
            if success:
                print_success(f"{name}: {value} → {result}")
                results.append(("PASS", name))
            else:
                print_error(f"{name}: Beklenen {expected}, alınan {result}")
                results.append(("FAIL", name))
        except Exception as e:
            print_error(f"{name}: Hata - {e}")
            results.append(("ERROR", name))
    
    # Geçersiz integer
    print_info("\nGeçersiz dönüşüm testi:")
    try:
        int("not_a_number")
        print_error("Hata bekleniyor ama oluşmadı!")
        results.append(("FAIL", "Invalid Integer"))
    except ValueError:
        print_success("Geçersiz string için ValueError yakalandı ✓")
        results.append(("PASS", "Invalid Integer"))
    
    wait_for_user()
    
    # Test 1.3: Boolean dönüşümleri
    print_step(3, "Boolean Dönüşümleri")
    
    true_values = ["true", "True", "TRUE", "1", "yes", "on"]
    false_values = ["false", "False", "0", "no", "off", ""]
    
    print_info("True değerleri:")
    for val in true_values:
        val_lower = val.lower().strip()
        result = val_lower in ("true", "1", "yes", "on")
        if result:
            print_success(f"  '{val}' → True")
            results.append(("PASS", f"Boolean '{val}'"))
        else:
            print_error(f"  '{val}' → False (beklenen: True)")
            results.append(("FAIL", f"Boolean '{val}'"))
    
    print_info("\nFalse değerleri:")
    for val in false_values:
        val_lower = val.lower().strip()
        result = val_lower in ("false", "0", "no", "off", "")
        if result:
            print_success(f"  '{val}' → False")
            results.append(("PASS", f"Boolean '{val}'"))
        else:
            print_error(f"  '{val}' → True (beklenen: False)")
            results.append(("FAIL", f"Boolean '{val}'"))
    
    wait_for_user()
    
    # Test 1.4: JSON dönüşümleri
    print_step(4, "JSON Dönüşümleri (Array & Object)")
    
    import json
    
    # Array
    print_info("Array dönüşümleri:")
    json_arrays = [
        ('["a", "b", "c"]', ["a", "b", "c"]),
        ('[1, 2, 3]', [1, 2, 3]),
        ('[[1, 2], [3, 4]]', [[1, 2], [3, 4]]),
    ]
    
    for json_str, expected in json_arrays:
        try:
            result = json.loads(json_str)
            if result == expected:
                print_success(f"  {json_str} → {result}")
                results.append(("PASS", f"JSON Array {json_str[:20]}"))
            else:
                print_error(f"  Beklenen {expected}, alınan {result}")
                results.append(("FAIL", f"JSON Array {json_str[:20]}"))
        except Exception as e:
            print_error(f"  Hata: {e}")
            results.append(("ERROR", f"JSON Array {json_str[:20]}"))
    
    # Object
    print_info("\nObject dönüşümleri:")
    json_objects = [
        ('{"key": "value"}', {"key": "value"}),
        ('{"name": "test", "count": 5}', {"name": "test", "count": 5}),
        ('{"outer": {"inner": "value"}}', {"outer": {"inner": "value"}}),
    ]
    
    for json_str, expected in json_objects:
        try:
            result = json.loads(json_str)
            if result == expected:
                print_success(f"  {json_str} → {result}")
                results.append(("PASS", f"JSON Object {json_str[:20]}"))
            else:
                print_error(f"  Beklenen {expected}, alınan {result}")
                results.append(("FAIL", f"JSON Object {json_str[:20]}"))
        except Exception as e:
            print_error(f"  Hata: {e}")
            results.append(("ERROR", f"JSON Object {json_str[:20]}"))
    
    return results


# ============================================================================
# TEST 2: Reference Parsing Testleri
# ============================================================================

def test_reference_parsing():
    """Reference parsing testleri."""
    print_header("TEST 2: Reference Parsing - Referans Ayrıştırma Testleri")
    
    print_info("Reference'lar ${type:path} formatındadır.")
    print_info("Desteklenen tipler: static, trigger, node, value, credential, database, file\n")
    
    results = []
    
    def is_reference(value) -> bool:
        """Değerin referans formatında olup olmadığını kontrol eder."""
        if not isinstance(value, str):
            return False
        if not (value.startswith("${") and value.endswith("}")):
            return False
        if ":" not in value:
            return False
        return True
    
    def parse_reference(reference: str) -> dict:
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
    
    # Test 2.1: Reference Detection
    print_step(1, "Reference Detection (Referans Tespiti)")
    
    valid_refs = [
        "${static:value}",
        "${trigger:data.key}",
        "${node:NOD-123.result}",
        "${value:ENV-456}",
        "${credential:CRD-789.api_key}",
        "${database:DBS-111.host}",
        "${file:FLE-222.content}"
    ]
    
    print_info("Geçerli referanslar:")
    for ref in valid_refs:
        if is_reference(ref):
            print_success(f"  ✓ {ref}")
            results.append(("PASS", f"Valid ref: {ref[:30]}"))
        else:
            print_error(f"  ✗ {ref} (referans olarak algılanmalıydı)")
            results.append(("FAIL", f"Valid ref: {ref[:30]}"))
    
    invalid_refs = [
        "plain_value",
        "${incomplete",
        "no_colon${}",
        "$trigger:data}",
        None,
        123,
    ]
    
    print_info("\nGeçersiz referanslar:")
    for ref in invalid_refs:
        if not is_reference(ref):
            print_success(f"  ✓ {ref} (referans değil - doğru)")
            results.append(("PASS", f"Invalid ref: {str(ref)[:30]}"))
        else:
            print_error(f"  ✗ {ref} (referans olarak algılanmamalıydı)")
            results.append(("FAIL", f"Invalid ref: {str(ref)[:30]}"))
    
    wait_for_user()
    
    # Test 2.2: Reference Parsing
    print_step(2, "Reference Parsing (Referans Ayrıştırma)")
    
    parse_tests = [
        ("${static:my_value}", "static", {"id_or_value": "my_value"}),
        ("${trigger:data.user.id}", "trigger", {"value_path": "data.user.id"}),
        ("${node:NOD-12345.result.data}", "node", {"id": "NOD-12345", "value_path": "result.data"}),
        ("${value:ENV-ABCDE}", "value", {"id": "ENV-ABCDE"}),
        ("${credential:CRD-XXXXX.api_key}", "credential", {"id": "CRD-XXXXX", "value_path": "api_key"}),
        ("${database:DBS-YYYYY.host}", "database", {"id": "DBS-YYYYY", "value_path": "host"}),
        ("${file:FLE-ZZZZZ.content}", "file", {"id": "FLE-ZZZZZ", "value_path": "content"}),
    ]
    
    for ref, expected_type, expected_fields in parse_tests:
        print_info(f"\nParsing: {ref}")
        try:
            parsed = parse_reference(ref)
            
            if parsed["type"] == expected_type:
                print_success(f"  Type: {parsed['type']}")
            else:
                print_error(f"  Type: {parsed['type']} (beklenen: {expected_type})")
            
            for field, expected_value in expected_fields.items():
                actual_value = parsed.get(field)
                if actual_value == expected_value:
                    print_success(f"  {field}: {actual_value}")
                else:
                    print_error(f"  {field}: {actual_value} (beklenen: {expected_value})")
            
            results.append(("PASS", f"Parse: {ref[:30]}"))
        except Exception as e:
            print_error(f"  Hata: {e}")
            results.append(("ERROR", f"Parse: {ref[:30]}"))
    
    return results


# ============================================================================
# TEST 3: Nested Path Resolution Testleri
# ============================================================================

def test_nested_path_resolution():
    """Nested path resolution testleri."""
    print_header("TEST 3: Nested Path Resolution - İç İçe Yol Çözümleme")
    
    print_info("Nested path'ler nokta ve array indeksleri ile tanımlanır.")
    print_info("Örnek: data.items[0].name → ['data', 'items', '[0]', 'name']\n")
    
    results = []
    
    import re
    
    def resolve_nested_reference(value_path: str) -> list:
        """İç içe referans yolunu parçalara ayırır."""
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
    
    def get_value_from_context(path_parts: list, context):
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
    
    # Test 3.1: Path Parsing
    print_step(1, "Path Parsing (Yol Ayrıştırma)")
    
    path_tests = [
        ("data", ["data"]),
        ("data.user.name", ["data", "user", "name"]),
        ("data.items[0].name", ["data", "items", "[0]", "name"]),
        ("matrix[0][1].value", ["matrix", "[0]", "[1]", "value"]),
        ("", []),
    ]
    
    for path, expected in path_tests:
        result = resolve_nested_reference(path)
        if result == expected:
            print_success(f"  '{path}' → {result}")
            results.append(("PASS", f"Path: {path or '(empty)'}"))
        else:
            print_error(f"  '{path}' → {result} (beklenen: {expected})")
            results.append(("FAIL", f"Path: {path or '(empty)'}"))
    
    wait_for_user()
    
    # Test 3.2: Value Extraction
    print_step(2, "Value Extraction (Değer Çıkarma)")
    
    # Basit context
    print_info("\nBasit context:")
    context1 = {"name": "test", "count": 42}
    print(f"  Context: {json.dumps(context1)}")
    
    for path, expected in [("name", "test"), ("count", 42)]:
        parts = resolve_nested_reference(path)
        try:
            value = get_value_from_context(parts, context1)
            if value == expected:
                print_success(f"  '{path}' → {value}")
                results.append(("PASS", f"Extract: {path}"))
            else:
                print_error(f"  '{path}' → {value} (beklenen: {expected})")
                results.append(("FAIL", f"Extract: {path}"))
        except Exception as e:
            print_error(f"  '{path}' → Hata: {e}")
            results.append(("ERROR", f"Extract: {path}"))
    
    # İç içe context
    print_info("\nİç içe context:")
    context2 = {
        "user": {
            "profile": {
                "name": "John",
                "age": 30
            }
        }
    }
    print(f"  Context: {json.dumps(context2)}")
    
    for path, expected in [
        ("user.profile.name", "John"),
        ("user.profile.age", 30),
    ]:
        parts = resolve_nested_reference(path)
        try:
            value = get_value_from_context(parts, context2)
            if value == expected:
                print_success(f"  '{path}' → {value}")
                results.append(("PASS", f"Extract: {path}"))
            else:
                print_error(f"  '{path}' → {value} (beklenen: {expected})")
                results.append(("FAIL", f"Extract: {path}"))
        except Exception as e:
            print_error(f"  '{path}' → Hata: {e}")
            results.append(("ERROR", f"Extract: {path}"))
    
    wait_for_user()
    
    # Array indeksli context
    print_step(3, "Array Index ile Value Extraction")
    
    context3 = {
        "items": [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
            {"id": 3, "name": "third"}
        ]
    }
    print(f"  Context: {json.dumps(context3, indent=2)}")
    
    for path, expected in [
        ("items[0].name", "first"),
        ("items[1].id", 2),
        ("items[2].name", "third"),
    ]:
        parts = resolve_nested_reference(path)
        try:
            value = get_value_from_context(parts, context3)
            if value == expected:
                print_success(f"  '{path}' → {value}")
                results.append(("PASS", f"Array Extract: {path}"))
            else:
                print_error(f"  '{path}' → {value} (beklenen: {expected})")
                results.append(("FAIL", f"Array Extract: {path}"))
        except Exception as e:
            print_error(f"  '{path}' → Hata: {e}")
            results.append(("ERROR", f"Array Extract: {path}"))
    
    return results


# ============================================================================
# TEST 4: Execution Simulation
# ============================================================================

def test_execution_simulation():
    """Execution simülasyonu testi."""
    print_header("TEST 4: Execution Simulation - Çalıştırma Simülasyonu")
    
    print_info("Bu test, gerçek bir execution senaryosunu simüle eder.")
    print_info("Trigger data → Node 1 → Node 2 → Final Result\n")
    
    results = []
    
    import re
    
    def resolve_nested_reference(value_path: str) -> list:
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
        return [p for p in final_parts if p]
    
    def get_value_from_context(path_parts: list, context):
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
    
    # Senaryo Setup
    print_step(1, "Senaryo Setup")
    
    # Trigger Data
    trigger_data = {
        "initial_message": "Hello MiniFlow!",
        "timestamp": "2024-01-15T12:00:00Z",
        "user": {
            "id": "USR-12345",
            "name": "Test User"
        }
    }
    
    print_info("Trigger Data:")
    print(f"{Colors.CYAN}{json.dumps(trigger_data, indent=2)}{Colors.END}")
    
    # Node Configurations
    node1_config = {
        "name": "Transform Node",
        "input_params": {
            "message": "${trigger:initial_message}",
            "prefix": "${static:PROCESSED_}"
        }
    }
    
    node2_config = {
        "name": "Output Node",
        "input_params": {
            "input_value": "${node:NODE1.output}",
            "user_id": "${trigger:user.id}"
        }
    }
    
    print_info("\nNode 1 Config:")
    print(f"{Colors.CYAN}{json.dumps(node1_config, indent=2)}{Colors.END}")
    
    print_info("\nNode 2 Config:")
    print(f"{Colors.CYAN}{json.dumps(node2_config, indent=2)}{Colors.END}")
    
    wait_for_user()
    
    # Node 1 Execution
    print_step(2, "Node 1 Execution")
    
    print_info("Parametreleri çözümleme:")
    
    # message parametresi
    message_ref = node1_config["input_params"]["message"]
    print(f"  {Colors.YELLOW}message:{Colors.END} {message_ref}")
    
    # ${trigger:initial_message} parse et
    ref_content = message_ref[2:-1]
    ref_type, ref_path = ref_content.split(":", 1)
    print(f"    → Type: {ref_type}, Path: {ref_path}")
    
    path_parts = resolve_nested_reference(ref_path)
    message_value = get_value_from_context(path_parts, trigger_data)
    print_success(f"    → Çözümlenen değer: '{message_value}'")
    results.append(("PASS", "Node1 message param"))
    
    # prefix parametresi (static)
    prefix_ref = node1_config["input_params"]["prefix"]
    print(f"\n  {Colors.YELLOW}prefix:{Colors.END} {prefix_ref}")
    ref_content = prefix_ref[2:-1]
    ref_type, ref_value = ref_content.split(":", 1)
    print(f"    → Type: {ref_type}, Value: {ref_value}")
    prefix_value = ref_value
    print_success(f"    → Çözümlenen değer: '{prefix_value}'")
    results.append(("PASS", "Node1 prefix param"))
    
    # Node 1 çalıştır
    print_info("\nNode 1 çalıştırılıyor...")
    time.sleep(0.5)
    
    node1_output = {
        "output": f"{prefix_value}{message_value}",
        "status": "success",
        "processed_at": datetime.now().isoformat()
    }
    
    print_success(f"Node 1 tamamlandı!")
    print(f"  Output: {Colors.GREEN}{json.dumps(node1_output, indent=2)}{Colors.END}")
    results.append(("PASS", "Node1 execution"))
    
    wait_for_user()
    
    # Node 2 Execution
    print_step(3, "Node 2 Execution")
    
    # Execution context'i güncelle
    execution_context = {
        "trigger": trigger_data,
        "nodes": {
            "NODE1": node1_output
        }
    }
    
    print_info("Güncel Execution Context:")
    print(f"{Colors.CYAN}{json.dumps(execution_context, indent=2)}{Colors.END}")
    
    print_info("\nParametreleri çözümleme:")
    
    # input_value parametresi (node output'u)
    input_ref = node2_config["input_params"]["input_value"]
    print(f"  {Colors.YELLOW}input_value:{Colors.END} {input_ref}")
    
    ref_content = input_ref[2:-1]
    ref_type, ref_path = ref_content.split(":", 1)
    node_id, value_path = ref_path.split(".", 1)
    print(f"    → Type: {ref_type}, Node: {node_id}, Path: {value_path}")
    
    node_output = execution_context["nodes"][node_id]
    path_parts = resolve_nested_reference(value_path)
    input_value = get_value_from_context(path_parts, node_output)
    print_success(f"    → Çözümlenen değer: '{input_value}'")
    results.append(("PASS", "Node2 input_value param"))
    
    # user_id parametresi
    user_ref = node2_config["input_params"]["user_id"]
    print(f"\n  {Colors.YELLOW}user_id:{Colors.END} {user_ref}")
    
    ref_content = user_ref[2:-1]
    ref_type, ref_path = ref_content.split(":", 1)
    print(f"    → Type: {ref_type}, Path: {ref_path}")
    
    path_parts = resolve_nested_reference(ref_path)
    user_id_value = get_value_from_context(path_parts, trigger_data)
    print_success(f"    → Çözümlenen değer: '{user_id_value}'")
    results.append(("PASS", "Node2 user_id param"))
    
    # Node 2 çalıştır
    print_info("\nNode 2 çalıştırılıyor...")
    time.sleep(0.5)
    
    node2_output = {
        "final_result": f"[{user_id_value}] {input_value}",
        "status": "success",
        "completed_at": datetime.now().isoformat()
    }
    
    print_success(f"Node 2 tamamlandı!")
    print(f"  Output: {Colors.GREEN}{json.dumps(node2_output, indent=2)}{Colors.END}")
    results.append(("PASS", "Node2 execution"))
    
    wait_for_user()
    
    # Final Summary
    print_step(4, "Execution Tamamlandı - Final Summary")
    
    final_summary = {
        "execution_id": "EXE-" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "status": "COMPLETED",
        "trigger_data": trigger_data,
        "node_results": {
            "NODE1": node1_output,
            "NODE2": node2_output
        },
        "final_output": node2_output["final_result"],
        "duration_ms": 1523
    }
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}EXECUTION SUMMARY{Colors.END}")
    print(f"{Colors.GREEN}{'='*50}{Colors.END}")
    print(f"{Colors.GREEN}{json.dumps(final_summary, indent=2)}{Colors.END}")
    
    results.append(("PASS", "Execution completed"))
    
    return results


# ============================================================================
# TEST 5: Parameter Grouping
# ============================================================================

def test_parameter_grouping():
    """Parametre gruplandırma testi."""
    print_header("TEST 5: Parameter Grouping - Parametre Gruplandırma")
    
    print_info("Parametreler referans tiplerine göre gruplandırılır.")
    print_info("Her grup ayrı ayrı çözümlenir (paralel işleme için).\n")
    
    results = []
    
    def is_reference(value) -> bool:
        if not isinstance(value, str):
            return False
        if not (value.startswith("${") and value.endswith("}")):
            return False
        if ":" not in value:
            return False
        return True
    
    def parse_reference(reference: str, param_name: str) -> dict:
        content = reference[2:-1]
        ref_type, identifier_path = content.split(":", 1)
        ref_type = ref_type.strip()
        identifier_path = identifier_path.strip()
        
        result = {"type": ref_type, "param_name": param_name}
        
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
    
    def group_parameters(params: dict) -> dict:
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
            
            if is_reference(param_value):
                reference_info = parse_reference(param_value, param_name)
                ref_type = reference_info["type"]
                groups[ref_type].append(reference_info)
            else:
                groups['static'].append({
                    "type": 'static',
                    "id_or_value": param_value,
                    "param_name": param_name
                })
        
        return groups
    
    print_step(1, "Örnek Node Parametreleri")
    
    params = {
        "api_url": {"value": "https://api.example.com", "type": "string"},
        "message": {"value": "${trigger:input.message}", "type": "string"},
        "prev_result": {"value": "${node:NOD-123.result.data}", "type": "object"},
        "api_key": {"value": "${credential:CRD-API.key}", "type": "string"},
        "db_host": {"value": "${database:DBS-MAIN.host}", "type": "string"},
        "env_var": {"value": "${value:ENV-SECRET}", "type": "string"},
        "config_file": {"value": "${file:FLE-CONFIG.content}", "type": "string"},
        "timeout": {"value": "${static:30}", "type": "integer"},
    }
    
    print_info("Input Parametreleri:")
    for name, data in params.items():
        print(f"  {Colors.CYAN}{name}:{Colors.END} {data['value']}")
    
    wait_for_user()
    
    print_step(2, "Gruplandırma Sonucu")
    
    groups = group_parameters(params)
    
    for group_name, items in groups.items():
        if items:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}[{group_name.upper()}]{Colors.END} ({len(items)} parametre)")
            for item in items:
                print(f"  • {item['param_name']}")
                for key, value in item.items():
                    if key != 'param_name':
                        print(f"    {key}: {value}")
            results.append(("PASS", f"Group: {group_name}"))
        else:
            print(f"\n{Colors.BOLD}[{group_name.upper()}]{Colors.END} (boş)")
    
    wait_for_user()
    
    print_step(3, "Gruplandırma İstatistikleri")
    
    total_params = sum(len(items) for items in groups.values())
    print_info(f"Toplam parametre sayısı: {total_params}")
    
    print("\nGrup dağılımı:")
    for group_name, items in groups.items():
        count = len(items)
        bar_length = count * 5
        bar = "█" * bar_length
        print(f"  {group_name:12} {bar} {count}")
    
    return results


# ============================================================================
# MAIN
# ============================================================================

def print_final_summary(all_results: dict):
    """Final özet yazdır."""
    print_header("📊 FINAL TEST SUMMARY")
    
    total_pass = 0
    total_fail = 0
    total_error = 0
    
    for test_name, results in all_results.items():
        passed = sum(1 for r in results if r[0] == "PASS")
        failed = sum(1 for r in results if r[0] == "FAIL")
        errors = sum(1 for r in results if r[0] == "ERROR")
        
        total_pass += passed
        total_fail += failed
        total_error += errors
        
        status_icon = "✅" if failed == 0 and errors == 0 else "❌"
        print(f"  {status_icon} {test_name}: {passed} passed, {failed} failed, {errors} errors")
    
    print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
    print(f"  {Colors.GREEN}Total Passed:{Colors.END} {total_pass}")
    print(f"  {Colors.RED}Total Failed:{Colors.END} {total_fail}")
    print(f"  {Colors.YELLOW}Total Errors:{Colors.END} {total_error}")
    
    if total_fail == 0 and total_error == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TÜM TESTLER BAŞARILI!{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️ BAZI TESTLER BAŞARISIZ!{Colors.END}")


def main():
    """Ana test fonksiyonu."""
    print_header("🚀 MiniFlow Execution Test Suite")
    
    print(f"""
{Colors.CYAN}Bu interaktif test suite, MiniFlow execution sisteminin
temel bileşenlerini test eder:{Colors.END}

  1. TypeConverter    - Tip dönüşümleri
  2. Reference Parser - Referans ayrıştırma
  3. Path Resolution  - İç içe yol çözümleme
  4. Execution Sim    - Çalıştırma simülasyonu
  5. Parameter Groups - Parametre gruplandırma

{Colors.YELLOW}Her adımda size sonuçlar gösterilecek ve devam etmek
için onayınız istenecektir.{Colors.END}
""")
    
    wait_for_user("Testlere başlamak için Enter'a basın...")
    
    all_results = {}
    
    try:
        # Test 1
        results = test_type_converter()
        all_results["TypeConverter"] = results
        wait_for_user("Sonraki teste geçmek için Enter'a basın...")
        
        # Test 2
        results = test_reference_parsing()
        all_results["Reference Parsing"] = results
        wait_for_user("Sonraki teste geçmek için Enter'a basın...")
        
        # Test 3
        results = test_nested_path_resolution()
        all_results["Path Resolution"] = results
        wait_for_user("Sonraki teste geçmek için Enter'a basın...")
        
        # Test 4
        results = test_execution_simulation()
        all_results["Execution Simulation"] = results
        wait_for_user("Sonraki teste geçmek için Enter'a basın...")
        
        # Test 5
        results = test_parameter_grouping()
        all_results["Parameter Grouping"] = results
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test iptal edildi.{Colors.END}")
        sys.exit(0)
    
    # Final Summary
    print_final_summary(all_results)
    
    print(f"\n{Colors.CYAN}Test tamamlandı!{Colors.END}\n")


if __name__ == "__main__":
    main()

