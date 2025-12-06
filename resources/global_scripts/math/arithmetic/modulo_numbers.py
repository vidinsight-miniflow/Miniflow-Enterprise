"""
Matematik Script: Modulo (kalan) işlemi
"""
def module():
    class ModuloNumbers:
        def run(self, params):
            """
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
            """
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
