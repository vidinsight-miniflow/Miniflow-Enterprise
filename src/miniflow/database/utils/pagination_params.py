from typing import Generic, TypeVar, List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from math import ceil

from miniflow.core.exceptions import InvalidInputError


T = TypeVar('T')

@dataclass
class PaginationParams:
    """
    Parameters for pagination requests.
    
    Attributes:
        page: Page number (1-indexed)
        page_size: Number of items per page
        order_by: Field name to order by
        order_desc: Whether to order descendingly
        include_deleted: Whether to include soft-deleted records
    """
    page: int = 1
    page_size: int = 100
    order_by: Optional[str] = None
    order_desc: bool = False
    include_deleted: bool = False

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size
    
    def validate(self, max_page_size: int = 1000) -> None:
        if self.page < 1:
            raise InvalidInputError(field_name="page")
        
        if self.page_size < 1:
            raise InvalidInputError(field_name="page_size")
        
        if self.page_size > max_page_size:
            raise InvalidInputError(field_name="page_size")
        

@dataclass
class PaginationMetadata:
    """
    Metadata about pagination state.
    
    Attributes:
        page: Current page number
        page_size: Number of items per page
        total_items: Total number of items across all pages
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_prev: Whether there is a previous page
        next_page: Next page number (if exists)
        prev_page: Previous page number (if exists)
    """

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None

    @classmethod
    def from_params(cls, params: PaginationParams, total_items: int) -> 'PaginationMetadata':
        total_pages = ceil(total_items / params.page_size) if params.page_size > 0 else 0
        has_next = params.page < total_pages
        has_prev = params.page > 1

        return cls(
            page=params.page,
            page_size=params.page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=params.page + 1 if has_next else None,
            prev_page=params.page - 1 if has_prev else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
            "next_page": self.next_page,
            "prev_page": self.prev_page
        }
    
@dataclass
class PaginatedResponse(Generic[T]):
    items: List[T]
    metadata: PaginationMetadata

    def to_dict(
        self,
        serialize_items: bool = False,
        exclude_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        
        if serialize_items:
            serialized_items = []
            for item in self.items:
                if hasattr(item, 'to_dict'):
                    serialized_items.append(item.to_dict(exclude_fields=exclude_fields))
                else:
                    serialized_items.append(item)
            items_data = serialized_items
        else:
            items_data = self.items
        
        return {
            "items": items_data,
            "metadata": self.metadata.to_dict()
        }
    
    @property
    def count(self) -> int:
        return len(self.items)
    
    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __iter__(self):
        return iter(self.items)
    
    def __getitem__(self, index: int) -> T:
        return self.items[index]
    

def create_pagination_params(
    page: int = 1,
    page_size: int = 100,
    order_by: Optional[str] = None,
    order_desc: bool = False,
    include_deleted: bool = False
) -> PaginationParams:
    """
    Helper function to create pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        order_by: Field name to order by
        order_desc: If True, order descending
        include_deleted: Whether to include soft-deleted records
    
    Returns:
        PaginationParams instance
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted
    )