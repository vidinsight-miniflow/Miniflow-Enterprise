"""
Matematik Script: İki sayıyı çıkar
"""
def module():
    class SubtractNumbers:
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
                    "operation": "subtract"
                }
            """
            a = params.get("a", 0)
            b = params.get("b", 0)
            result = a - b
            
            return {
                "result": result,
                "operation": "subtract",
                "inputs": {"a": a, "b": b}
            }
    
    return SubtractNumbers()
