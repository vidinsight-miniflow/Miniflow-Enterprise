"""
File request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class UpdateFileRequest(BaseModel):
    """Request schema for updating file metadata."""
    name: Optional[str] = Field(None, description="File name", min_length=1)
    description: Optional[str] = Field(None, description="File description")
    tags: Optional[List[str]] = Field(None, description="Tags")

