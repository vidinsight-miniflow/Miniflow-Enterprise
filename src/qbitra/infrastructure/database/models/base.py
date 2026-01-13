import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase, declared_attr


class BaseModel(DeclarativeBase):
    __allow_unmapped__ = True
    __abstract__ = True
    __prefix__ = "GEN"

    @declared_attr
    def id(cls):
        return Column(String(20), primary_key=True, default=cls._generate_id, nullable=False)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__allow_unmapped__ = True

    @classmethod
    def _generate_id(cls):
        prefix = getattr(cls, '__prefix__', 'GEN')
        if len(prefix) != 3:
            raise ValueError(f"Model prefix must be exactly 3 characters. Got: {prefix}")
        
        uuid_suffix = str(uuid.uuid4()).replace('-', '')[:16].upper()
        return f"{prefix}-{uuid_suffix}"