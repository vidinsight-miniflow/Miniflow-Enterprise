from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

@dataclass
class FilterParams:
    """
    Parameters for advanced filtering.
    
    Attributes:
        filters: Dictionary of field:value filters
        operators: Dictionary of field:operator mappings
        search: Optional search term for text search
        search_fields: Fields to search in when search term is provided
    """
    filters: Dict[str, Any] = field(default_factory=dict)
    operators: Dict[str, str] = field(default_factory=dict)
    search: Optional[str] = None
    search_fields: List[str] = field(default_factory=list)
    
    def add_filter(self, field: str, value: Any, operator: str = "eq") -> None:
        """
        Add a filter with operator.
        
        Args:
            field: Field name to filter
            value: Value to filter by
            operator: Operator to use (eq, ne, gt, gte, lt, lte, in, like, ilike)
        """
        self.filters[field] = value
        self.operators[field] = operator
    
    def add_equality_filter(self, field: str, value: Any) -> None:
        """Add an equality filter (field = value)"""
        self.add_filter(field, value, "eq")
    
    def add_in_filter(self, field: str, values: List[Any]) -> None:
        """Add an IN filter (field IN values)"""
        self.add_filter(field, values, "in")
    
    def add_like_filter(self, field: str, pattern: str, case_sensitive: bool = False) -> None:
        """Add a LIKE filter for pattern matching"""
        operator = "like" if case_sensitive else "ilike"
        self.add_filter(field, pattern, operator)
    
    def add_range_filter(self, field: str, min_value: Any = None, max_value: Any = None) -> None:
        """Add range filters (field >= min AND field <= max)"""
        if min_value is not None:
            self.add_filter(f"{field}_min", min_value, "gte")
        if max_value is not None:
            self.add_filter(f"{field}_max", max_value, "lte")
    
    def has_filters(self) -> bool:
        """Check if any filters are set"""
        return bool(self.filters) or bool(self.search)