"""
Matematik Script: Üs alma işlemi
"""
def module():
    class PowerNumbers:
        def run(self, params):
            """
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
            """
            base = params.get("base", 0)
            exponent = params.get("exponent", 1)
            result = base ** exponent
            
            return {
                "result": result,
                "operation": "power",
                "inputs": {"base": base, "exponent": exponent}
            }
    
    return PowerNumbers()
