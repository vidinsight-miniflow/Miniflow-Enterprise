"""
Matematik Script: İki sayıyı böl
"""
def module():
    class DivideNumbers:
        def run(self, params):
            """
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
            """
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
