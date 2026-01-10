"""
Global Script Seeds
==================

Başlangıçta sisteme eklenecek global script'ler.
Temel matematik işlemleri ve diğer yaygın kullanılan script'ler.
"""

# ============================================================================
# Matematik İşlemleri
# ============================================================================

ADD_NUMBERS_CONTENT = """\"\"\"
Matematik Script: İki sayıyı topla
\"\"\"
def module():
    class AddNumbers:
        def run(self, params):
            \"\"\"
            Args:
                params: {
                    "a": int,
                    "b": int
                }
            Returns:
                {
                    "result": int,
                    "operation": "add"
                }
            \"\"\"
            a = params.get("a", 0)
            b = params.get("b", 0)
            result = a + b
            
            return {
                "result": result,
                "operation": "add",
                "inputs": {"a": a, "b": b}
            }
    
    return AddNumbers()
"""

SUBTRACT_NUMBERS_CONTENT = """\"\"\"
Matematik Script: İki sayıyı çıkar
\"\"\"
def module():
    class SubtractNumbers:
        def run(self, params):
            \"\"\"
            Args:
                params: {
                    "a": int,
                    "b": int
                }
            Returns:
                {
                    "result": int,
                    "operation": "subtract"
                }
            \"\"\"
            a = params.get("a", 0)
            b = params.get("b", 0)
            result = a - b
            
            return {
                "result": result,
                "operation": "subtract",
                "inputs": {"a": a, "b": b}
            }
    
    return SubtractNumbers()
"""

MULTIPLY_NUMBERS_CONTENT = """\"\"\"
Matematik Script: İki sayıyı çarp
\"\"\"
def module():
    class MultiplyNumbers:
        def run(self, params):
            \"\"\"
            Args:
                params: {
                    "a": int,
                    "b": int
                }
            Returns:
                {
                    "result": int,
                    "operation": "multiply"
                }
            \"\"\"
            a = params.get("a", 1)
            b = params.get("b", 1)
            result = a * b
            
            return {
                "result": result,
                "operation": "multiply",
                "inputs": {"a": a, "b": b}
            }
    
    return MultiplyNumbers()
"""

DIVIDE_NUMBERS_CONTENT = """\"\"\"
Matematik Script: İki sayıyı böl
\"\"\"
def module():
    class DivideNumbers:
        def run(self, params):
            \"\"\"
            Args:
                params: {
                    "a": int,
                    "b": int
                }
            Returns:
                {
                    "result": float,
                    "operation": "divide"
                }
            \"\"\"
            a = params.get("a", 0)
            b = params.get("b", 1)
            
            if b == 0:
                return {
                    "result": None,
                    "operation": "divide",
                    "error": "Division by zero",
                    "inputs": {"a": a, "b": b}
                }
            
            result = a / b
            
            return {
                "result": result,
                "operation": "divide",
                "inputs": {"a": a, "b": b}
            }
    
    return DivideNumbers()
"""

POWER_NUMBERS_CONTENT = """\"\"\"
Matematik Script: Üs alma işlemi
\"\"\"
def module():
    class PowerNumbers:
        def run(self, params):
            \"\"\"
            Args:
                params: {
                    "base": int,
                    "exponent": int
                }
            Returns:
                {
                    "result": int,
                    "operation": "power"
                }
            \"\"\"
            base = params.get("base", 0)
            exponent = params.get("exponent", 1)
            result = base ** exponent
            
            return {
                "result": result,
                "operation": "power",
                "inputs": {"base": base, "exponent": exponent}
            }
    
    return PowerNumbers()
"""

MODULO_NUMBERS_CONTENT = """\"\"\"
Matematik Script: Modulo (kalan) işlemi
\"\"\"
def module():
    class ModuloNumbers:
        def run(self, params):
            \"\"\"
            Args:
                params: {
                    "a": int,
                    "b": int
                }
            Returns:
                {
                    "result": int,
                    "operation": "modulo"
                }
            \"\"\"
            a = params.get("a", 0)
            b = params.get("b", 1)
            
            if b == 0:
                return {
                    "result": None,
                    "operation": "modulo",
                    "error": "Modulo by zero",
                    "inputs": {"a": a, "b": b}
                }
            
            result = a % b
            
            return {
                "result": result,
                "operation": "modulo",
                "inputs": {"a": a, "b": b}
            }
    
    return ModuloNumbers()
"""

# ============================================================================
# Seed Data
# ============================================================================

GLOBAL_SCRIPT_SEEDS = [
    # Toplama
    {
        "name": "add_numbers",
        "category": "math",
        "subcategory": "arithmetic",
        "description": "İki sayıyı toplar",
        "content": ADD_NUMBERS_CONTENT,
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "İlk sayı"},
                "b": {"type": "integer", "description": "İkinci sayı"}
            },
            "required": ["a", "b"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "integer", "description": "Toplam sonucu"},
                "operation": {"type": "string", "description": "İşlem tipi"},
                "inputs": {"type": "object", "description": "Girdi değerleri"}
            }
        },
        "tags": ["math", "addition", "arithmetic", "basic"],
        "required_packages": []
    },
    
    # Çıkarma
    {
        "name": "subtract_numbers",
        "category": "math",
        "subcategory": "arithmetic",
        "description": "İki sayıyı çıkarır",
        "content": SUBTRACT_NUMBERS_CONTENT,
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "İlk sayı"},
                "b": {"type": "integer", "description": "İkinci sayı"}
            },
            "required": ["a", "b"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "integer", "description": "Fark sonucu"},
                "operation": {"type": "string", "description": "İşlem tipi"},
                "inputs": {"type": "object", "description": "Girdi değerleri"}
            }
        },
        "tags": ["math", "subtraction", "arithmetic", "basic"],
        "required_packages": []
    },
    
    # Çarpma
    {
        "name": "multiply_numbers",
        "category": "math",
        "subcategory": "arithmetic",
        "description": "İki sayıyı çarpar",
        "content": MULTIPLY_NUMBERS_CONTENT,
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "İlk sayı"},
                "b": {"type": "integer", "description": "İkinci sayı"}
            },
            "required": ["a", "b"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "integer", "description": "Çarpım sonucu"},
                "operation": {"type": "string", "description": "İşlem tipi"},
                "inputs": {"type": "object", "description": "Girdi değerleri"}
            }
        },
        "tags": ["math", "multiplication", "arithmetic", "basic"],
        "required_packages": []
    },
    
    # Bölme
    {
        "name": "divide_numbers",
        "category": "math",
        "subcategory": "arithmetic",
        "description": "İki sayıyı böler",
        "content": DIVIDE_NUMBERS_CONTENT,
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "Bölünen sayı"},
                "b": {"type": "integer", "description": "Bölen sayı"}
            },
            "required": ["a", "b"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "number", "description": "Bölüm sonucu"},
                "operation": {"type": "string", "description": "İşlem tipi"},
                "inputs": {"type": "object", "description": "Girdi değerleri"},
                "error": {"type": "string", "description": "Hata mesajı (varsa)"}
            }
        },
        "tags": ["math", "division", "arithmetic", "basic"],
        "required_packages": []
    },
    
    # Üs alma
    {
        "name": "power_numbers",
        "category": "math",
        "subcategory": "arithmetic",
        "description": "Üs alma işlemi yapar",
        "content": POWER_NUMBERS_CONTENT,
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "integer", "description": "Taban"},
                "exponent": {"type": "integer", "description": "Üs"}
            },
            "required": ["base", "exponent"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "integer", "description": "Üs alma sonucu"},
                "operation": {"type": "string", "description": "İşlem tipi"},
                "inputs": {"type": "object", "description": "Girdi değerleri"}
            }
        },
        "tags": ["math", "power", "exponent", "arithmetic"],
        "required_packages": []
    },
    
    # Modulo
    {
        "name": "modulo_numbers",
        "category": "math",
        "subcategory": "arithmetic",
        "description": "Modulo (kalan) işlemi yapar",
        "content": MODULO_NUMBERS_CONTENT,
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "İlk sayı"},
                "b": {"type": "integer", "description": "İkinci sayı"}
            },
            "required": ["a", "b"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "integer", "description": "Kalan sonucu"},
                "operation": {"type": "string", "description": "İşlem tipi"},
                "inputs": {"type": "object", "description": "Girdi değerleri"},
                "error": {"type": "string", "description": "Hata mesajı (varsa)"}
            }
        },
        "tags": ["math", "modulo", "remainder", "arithmetic"],
        "required_packages": []
    },
]

