"""
Matematik Script: İki sayıyı topla
"""
def module():
    class AddNumbers:
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
                    "operation": "add"
                }
            """
            a = params.get("a", 0)
            b = params.get("b", 0)
            result = a + b
            
            return {
                "result": result,
                "operation": "add",
                "inputs": {"a": a, "b": b}
            }
    
    return AddNumbers()
