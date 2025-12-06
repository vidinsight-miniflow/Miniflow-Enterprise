"""
FastAPI app factory for uvicorn reload support.

This module exports the app instance so that uvicorn reload can work properly.
Uvicorn reload requires an import string (e.g., 'src.miniflow.app:app') instead of an app object.

Note: This module is only used when reload=True. When reload=False, the app object
is passed directly to uvicorn.run() in __main__.py
"""
from .__main__ import MiniFlow

# Create MiniFlow instance and app
# This will be re-executed on each reload, which is expected behavior
_miniflow = MiniFlow()
app = _miniflow._create_fastapi_app()

