"""
Matematik Script: İki sayıyı çarp
"""
def module():
    class MultiplyNumbers:
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
                    "operation": "multiply"
                }
            """
            a = params.get("a", 1)
            b = params.get("b", 1)
            result = a * b
            
            return {
                "result": result,
                "operation": "multiply",
                "inputs": {"a": a, "b": b}
            }
    
    return MultiplyNumbers()
