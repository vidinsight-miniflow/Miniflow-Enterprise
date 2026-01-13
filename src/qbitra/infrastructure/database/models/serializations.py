"""Model Serializasyon: SQLAlchemy modellerini dict/JSON'a dönüştürme."""

from typing import List, Dict, Any, Optional, Set, Callable
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from enum import Enum
import json

# Tip bazlı serializer mapping - O(1) lookup
_SERIALIZERS: Dict[type, Callable[[Any], Any]] = {
    str: lambda v: v,
    int: lambda v: v,
    float: lambda v: v,
    bool: lambda v: v,
    type(None): lambda v: None,
    datetime: lambda v: v.isoformat(),
    date: lambda v: v.isoformat(),
    Decimal: lambda v: float(v),
    UUID: lambda v: str(v),
    bytes: lambda v: v.decode('utf-8', errors='ignore'),
}


def _serialize_value(value: Any) -> Any:
    """Değeri JSON-serializable formata dönüştürür - O(1) lookup."""
    # Direkt tip eşleşmesi - O(1)
    serializer = _SERIALIZERS.get(type(value))
    if serializer is not None:
        return serializer(value)

    # Enum kontrolü (inheritance nedeniyle ayrı)
    if isinstance(value, Enum):
        return value.value

    # Container tipler
    if isinstance(value, (list, dict)):
        return value

    if isinstance(value, (set, frozenset)):
        return list(value)

    # Fallback
    if hasattr(value, '__dict__'):
        return str(value)

    return value


def model_to_dict(
    instance: Any,
    exclude: Optional[List[str]] = None,
    include_relationships: bool = False,
    max_depth: int = 1,
    _exclude_set: Optional[Set[str]] = None,
    _visited: Optional[Set[int]] = None,
) -> Optional[Dict[str, Any]]:
    """SQLAlchemy model instance'ını dictionary'ye dönüştürür."""
    if instance is None:
        raise ValueError("Instance cannot be None")

    # Circular reference koruması - O(1)
    if _visited is None:
        _visited = set()

    instance_id = id(instance)
    if instance_id in _visited:
        return None

    _visited.add(instance_id)

    try:
        # Exclude set - O(1) lookup için
        if _exclude_set is None:
            _exclude_set = set(exclude) if exclude else set()
            _exclude_set.add('_sa_instance_state')

        result: Dict[str, Any] = {}

        # Kolonları serialize et - O(C)
        table = getattr(instance, '__table__', None)
        if table is not None:
            for column in table.columns:
                name = column.name
                if name not in _exclude_set and not name.startswith('_'):
                    result[name] = _serialize_value(getattr(instance, name, None))

        # Relationship'leri serialize et - O(R * L * D)
        if include_relationships and max_depth > 0:
            mapper = getattr(instance, '__mapper__', None)
            if mapper is not None:
                for rel in mapper.relationships:
                    rel_name = rel.key
                    if rel_name in _exclude_set:
                        continue

                    rel_value = getattr(instance, rel_name, None)

                    if rel_value is None:
                        result[rel_name] = None
                    elif isinstance(rel_value, list):
                        result[rel_name] = [
                            model_to_dict(
                                item,
                                include_relationships=include_relationships,
                                max_depth=max_depth - 1,
                                _exclude_set=_exclude_set,
                                _visited=_visited,
                            )
                            for item in rel_value
                        ]
                    else:
                        result[rel_name] = model_to_dict(
                            rel_value,
                            include_relationships=include_relationships,
                            max_depth=max_depth - 1,
                            _exclude_set=_exclude_set,
                            _visited=_visited,
                        )

        return result
    finally:
        _visited.discard(instance_id)


def models_to_list(
    instances: Optional[List[Any]],
    exclude: Optional[List[str]] = None,
    include_relationships: bool = False,
    max_depth: int = 1,
) -> List[Dict[str, Any]]:
    """SQLAlchemy model listesini dictionary listesine dönüştürür."""
    if not instances:
        return []

    # Exclude set bir kez oluştur - O(E)
    exclude_set = set(exclude) if exclude else set()
    exclude_set.add('_sa_instance_state')

    return [
        model_to_dict(
            instance,
            include_relationships=include_relationships,
            max_depth=max_depth,
            _exclude_set=exclude_set,
        )
        for instance in instances
    ]


def model_to_json(
    instance: Any,
    exclude: Optional[List[str]] = None,
    include_relationships: bool = False,
    indent: Optional[int] = None,
    ensure_ascii: bool = False,
) -> str:
    """SQLAlchemy model instance'ını JSON string'ine dönüştürür."""
    data = model_to_dict(
        instance,
        exclude=exclude,
        include_relationships=include_relationships,
    )

    return json.dumps(
        data,
        indent=indent,
        ensure_ascii=ensure_ascii,
        default=_serialize_value,
    )