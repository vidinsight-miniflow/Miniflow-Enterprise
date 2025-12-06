from typing import Optional, Dict, Any, List

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)


class NodeService:
    """
    Workflow Node yönetim servisi.
    
    Workflow node'larının CRUD işlemleri ve script bağlama işlemlerini sağlar.
    NOT: workflow_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _node_repo = _registry.node_repository()
    _workflow_repo = _registry.workflow_repository()
    _script_repo = _registry.script_repository()
    _custom_script_repo = _registry.custom_script_repository()
    _edge_repo = _registry.edge_repository()

    # ==================================================================================== HELPERS ==
    @classmethod
    def _map_schema_type_to_frontend_type(cls, schema_type: str) -> str:
        """Schema type'ı frontend input type'a map eder."""
        type_mapping = {
            "string": "text",
            "number": "number",
            "integer": "number",
            "float": "number",
            "boolean": "checkbox",
            "array": "textarea",
            "object": "textarea",
            "email": "email",
            "url": "url",
            "password": "password",
        }
        return type_mapping.get(schema_type.lower(), "text")

    @classmethod
    def _convert_schema_to_frontend_format(
        cls,
        input_schema: Dict[str, Any],
        existing_input_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Script'in input_schema'sını frontend formatına dönüştürür."""
        frontend_params = {}
        order = 0
        
        # JSON Schema formatı kontrolü: {"type": "object", "properties": {...}}
        if isinstance(input_schema, dict) and "properties" in input_schema:
            required_fields = input_schema.get("required", [])
            input_schema = input_schema["properties"]
            # Her property'ye required bilgisini ekle
            for prop_name in required_fields:
                if prop_name in input_schema and isinstance(input_schema[prop_name], dict):
                    input_schema[prop_name]["required"] = True
        
        # Eğer hala dict değilse, boş dict kullan
        if not isinstance(input_schema, dict):
            input_schema = {}
        
        for param_name, param_schema in input_schema.items():
            if not isinstance(param_schema, dict):
                if isinstance(param_schema, str):
                    param_schema = {"type": param_schema}
                else:
                    continue
            
            existing_value = None
            if existing_input_params and param_name in existing_input_params:
                existing_param = existing_input_params[param_name]
                if isinstance(existing_param, dict):
                    existing_value = existing_param.get('value')
                else:
                    existing_value = existing_param
            
            schema_type = param_schema.get('type', 'string')
            front_type = cls._map_schema_type_to_frontend_type(schema_type)
            
            if 'enum' in param_schema and param_schema['enum']:
                if front_type == "text":
                    front_type = "select"
            
            frontend_params[param_name] = {
                "front": {
                    "order": order,
                    "type": front_type,
                    "values": param_schema.get('enum'),
                    "placeholder": param_schema.get('placeholder') or param_schema.get('description') or f"Enter {param_name}..."
                },
                "type": schema_type,
                "default_value": existing_value if existing_value is not None else param_schema.get('default'),
                "value": existing_value,
                "required": param_schema.get('required', False),
                "description": param_schema.get('description')
            }
            order += 1
        
        return frontend_params

    @classmethod
    def _validate_and_convert_frontend_params(
        cls,
        frontend_params: Dict[str, Any],
        script_input_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Frontend form verilerini validate eder ve backend formatına dönüştürür."""
        validated_params = {}
        
        # JSON Schema formatı kontrolü: {"type": "object", "properties": {...}}
        required_fields = []
        if isinstance(script_input_schema, dict) and "properties" in script_input_schema:
            required_fields = script_input_schema.get("required", [])
            script_input_schema = script_input_schema["properties"]
            # Her property'ye required bilgisini ekle
            for prop_name in required_fields:
                if prop_name in script_input_schema and isinstance(script_input_schema[prop_name], dict):
                    script_input_schema[prop_name]["required"] = True
        
        # Eğer hala dict değilse, boş dict kullan
        if not isinstance(script_input_schema, dict):
            script_input_schema = {}
        
        for param_name, schema_def in script_input_schema.items():
            if isinstance(schema_def, str):
                schema_def = {"type": schema_def}
            
            if schema_def.get('required', False):
                if param_name not in frontend_params:
                    raise InvalidInputError(
                        field_name=param_name,
                        message=f"Required parameter '{param_name}' is missing"
                    )
        
        for param_name, param_data in frontend_params.items():
            if param_name not in script_input_schema:
                raise InvalidInputError(
                    field_name="input_params",
                    message=f"Parameter '{param_name}' is not defined in script's input_schema"
                )
            
            schema_def = script_input_schema[param_name]
            if isinstance(schema_def, str):
                schema_def = {"type": schema_def}
            
            value = None
            if isinstance(param_data, dict):
                value = param_data.get('value')
            else:
                value = param_data
            
            if schema_def.get('required', False) and (value is None or value == ''):
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Parameter '{param_name}' is required"
                )
            
            param_type = schema_def.get('type', 'string')
            if value is not None:
                cls._validate_param_type(param_name, value, param_type, schema_def)
            
            validated_params[param_name] = {
                "type": param_type,
                "value": value,
                "default_value": param_data.get('default_value') if isinstance(param_data, dict) else None,
                "required": schema_def.get('required', False),
                "description": param_data.get('description') if isinstance(param_data, dict) else schema_def.get('description')
            }
        
        return validated_params

    @classmethod
    def _is_reference(cls, value: Any) -> bool:
        """
        Değerin referans formatında olup olmadığını kontrol eder (${type:...}).
        
        Args:
            value: Kontrol edilecek değer
        
        Returns:
            bool: True (referans ise) veya False (değilse)
        """
        if not isinstance(value, str):
            return False
        if not (value.startswith("${") and value.endswith("}")):
            return False
        if ":" not in value:
            return False
        return True

    @classmethod
    def _validate_param_type(
        cls,
        param_name: str,
        value: Any,
        param_type: str,
        schema_def: Optional[Dict[str, Any]] = None
    ) -> None:
        """Parametre tipini validate eder."""
        # Reference string'leri validation'dan geçir (execution sırasında çözülecek)
        if cls._is_reference(value):
            return
        
        type_lower = param_type.lower()
        
        if schema_def and 'enum' in schema_def and schema_def['enum']:
            if value not in schema_def['enum']:
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Parameter '{param_name}' must be one of {schema_def['enum']}, got {value}"
                )
            return
        
        if type_lower in ('string', 'text'):
            if not isinstance(value, str):
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Parameter '{param_name}' must be a string"
                )
        elif type_lower in ('number', 'integer', 'float'):
            if not isinstance(value, (int, float)):
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Parameter '{param_name}' must be a number"
                )
        elif type_lower == 'boolean':
            if not isinstance(value, bool):
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Parameter '{param_name}' must be a boolean"
                )

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_node(
        cls,
        session,
        *,
        workflow_id: str,
        name: str,
        created_by: str,
        script_id: Optional[str] = None,
        custom_script_id: Optional[str] = None,
        description: Optional[str] = None,
        input_params: Optional[Dict[str, Any]] = None,
        output_params: Optional[Dict[str, Any]] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Yeni node oluşturur.
        
        - Ya script_id ya da custom_script_id verilmeli (XOR)
        - input_params script'in input_schema'sına göre validate edilir
        
        Args:
            workflow_id: Workflow ID'si
            name: Node adı (workflow içinde benzersiz)
            created_by: Oluşturan kullanıcı ID'si
            script_id: Global script ID (opsiyonel)
            custom_script_id: Custom script ID (opsiyonel)
            description: Açıklama (opsiyonel)
            input_params: Giriş parametreleri (opsiyonel)
            output_params: Çıkış parametreleri (opsiyonel)
            meta_data: Meta veriler (opsiyonel)
            max_retries: Maksimum tekrar sayısı (varsayılan: 3)
            timeout_seconds: Timeout süresi (varsayılan: 300)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Node name cannot be empty"
            )
        
        if max_retries < 0:
            raise InvalidInputError(
                field_name="max_retries",
                message="Max retries must be >= 0"
            )
        
        if timeout_seconds <= 0:
            raise InvalidInputError(
                field_name="timeout_seconds",
                message="Timeout must be > 0"
            )
        
        # Script XOR kontrolü
        if not script_id and not custom_script_id:
            raise InvalidInputError(
                field_name="script",
                message="Either script_id or custom_script_id must be provided"
            )
        if script_id and custom_script_id:
            raise InvalidInputError(
                field_name="script",
                message="Only one of script_id or custom_script_id can be provided"
            )
        
        # Workflow kontrolü
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        # Benzersizlik kontrolü
        existing = cls._node_repo._get_by_name(
            session,
            workflow_id=workflow_id,
            name=name
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Node",
                conflicting_field="name",
                message=f"Node with name '{name}' already exists in workflow {workflow_id}"
            )
        
        # Script kontrolü
        script = None
        custom_script = None
        
        if script_id:
            script = cls._script_repo._get_by_id(session, record_id=script_id)
            if not script:
                raise ResourceNotFoundError(
                resource_name="Script",
                    resource_id=script_id
                )
        
        if custom_script_id:
            custom_script = cls._custom_script_repo._get_by_id(session, record_id=custom_script_id)
            if not custom_script:
                raise ResourceNotFoundError(
                resource_name="CustomScript",
                    resource_id=custom_script_id
                )
            # Aynı workspace kontrolü
            if custom_script.workspace_id != workflow.workspace_id:
                raise InvalidInputError(
                    field_name="custom_script_id",
                    message="Custom script does not belong to the same workspace as workflow"
                )
        
        # Input params validation
        validated_input_params = input_params or {}
        executable_script = script or custom_script
        if executable_script and input_params:
            validated_input_params = cls._validate_and_convert_frontend_params(
                frontend_params=input_params,
                script_input_schema=executable_script.input_schema or {}
            )
        
        # Node oluştur
        node = cls._node_repo._create(
            session,
            workflow_id=workflow_id,
            name=name,
            script_id=script_id,
            custom_script_id=custom_script_id,
            description=description,
            input_params=validated_input_params,
            output_params=output_params or {},
            meta_data=meta_data or {},
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            created_by=created_by
        )
        
        return {"id": node.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_node(
        cls,
        session,
        *,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Node detaylarını getirir.
        
        Args:
            node_id: Node ID'si
            
        Returns:
            Node detayları
        """
        node = cls._node_repo._get_by_id(session, record_id=node_id)
        
        if not node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=node_id
            )
        
        return {
            "id": node.id,
            "workflow_id": node.workflow_id,
            "name": node.name,
            "description": node.description,
            "script_id": node.script_id,
            "custom_script_id": node.custom_script_id,
            "script_type": "GLOBAL" if node.script_id else "CUSTOM" if node.custom_script_id else None,
            "input_params": node.input_params or {},
            "output_params": node.output_params or {},
            "meta_data": node.meta_data or {},
            "max_retries": node.max_retries,
            "timeout_seconds": node.timeout_seconds,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
            "created_by": node.created_by
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_node_form_schema(
        cls,
        session,
        *,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Node'un frontend form şemasını getirir.
        
        Args:
            node_id: Node ID'si
            
        Returns:
            Form şeması
        """
        node = cls._node_repo._get_by_id(session, record_id=node_id)
        
        if not node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=node_id
            )
        
        # Script'i al
        script = None
        if node.script_id:
            script = cls._script_repo._get_by_id(session, record_id=node.script_id)
        elif node.custom_script_id:
            script = cls._custom_script_repo._get_by_id(session, record_id=node.custom_script_id)
        
        if not script:
            raise InvalidInputError(
                field_name="node",
                message="Node has no associated script"
            )
        
        frontend_schema = cls._convert_schema_to_frontend_format(
            input_schema=script.input_schema or {},
            existing_input_params=node.input_params
        )
        
        return {
            "node_id": node.id,
            "node_name": node.name,
            "script_id": node.script_id,
            "custom_script_id": node.custom_script_id,
            "script_name": script.name,
            "script_type": "GLOBAL" if node.script_id else "CUSTOM",
            "form_schema": frontend_schema,
            "output_schema": script.output_schema or {}
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workflow_nodes(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'un node'larını listeler.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"workflow_id": str, "nodes": List[Dict], "count": int}
        """
        nodes = cls._node_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "description": n.description,
                    "script_id": n.script_id,
                    "custom_script_id": n.custom_script_id,
                    "script_type": "GLOBAL" if n.script_id else "CUSTOM" if n.custom_script_id else None,
                    "max_retries": n.max_retries,
                    "timeout_seconds": n.timeout_seconds,
                    "meta_data": n.meta_data
                }
                for n in nodes
            ],
            "count": len(nodes)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_node(
        cls,
        session,
        *,
        node_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        script_id: Optional[str] = None,
        custom_script_id: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Node bilgilerini günceller.
        
        NOT: Script değiştirilirse input_params sıfırlanabilir.
        
        Args:
            node_id: Node ID'si
            name: Yeni ad (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            script_id: Yeni global script ID (opsiyonel)
            custom_script_id: Yeni custom script ID (opsiyonel)
            meta_data: Yeni meta veriler (opsiyonel)
            max_retries: Yeni max retries (opsiyonel)
            timeout_seconds: Yeni timeout (opsiyonel)
            
        Returns:
            Güncellenmiş node bilgileri
        """
        node = cls._node_repo._get_by_id(session, record_id=node_id)
        
        if not node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=node_id
            )
        
        # Validasyonlar
        if name is not None:
            if not name.strip():
                raise InvalidInputError(
                    field_name="name",
                    message="Node name cannot be empty"
                )
            if name != node.name:
                existing = cls._node_repo._get_by_name(
                    session,
                    workflow_id=node.workflow_id,
                    name=name
                )
                if existing:
                    raise ResourceAlreadyExistsError(
                        resource_name="Node",
                        conflicting_field="name",
                        message=f"Node with name '{name}' already exists in workflow {node.workflow_id}"
                    )
        
        if max_retries is not None and max_retries < 0:
            raise InvalidInputError(
                field_name="max_retries",
                message="Max retries must be >= 0"
            )
        
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise InvalidInputError(
                field_name="timeout_seconds",
                message="Timeout must be > 0"
            )
        
        # Script değişikliği kontrolü
        new_script_id = script_id if script_id is not None else node.script_id
        new_custom_script_id = custom_script_id if custom_script_id is not None else node.custom_script_id
        
        if new_script_id and new_custom_script_id:
            raise InvalidInputError(
                field_name="script",
                message="Only one of script_id or custom_script_id can be set"
            )
        if not new_script_id and not new_custom_script_id:
            raise InvalidInputError(
                field_name="script",
                message="Either script_id or custom_script_id must be set"
            )
        
        # Script kontrolleri
        if script_id is not None and script_id != node.script_id:
            script = cls._script_repo._get_by_id(session, record_id=script_id)
            if not script:
                raise ResourceNotFoundError(
                resource_name="Script",
                    resource_id=script_id
                )
        
        if custom_script_id is not None and custom_script_id != node.custom_script_id:
            workflow = cls._workflow_repo._get_by_id(session, record_id=node.workflow_id)
            custom_script = cls._custom_script_repo._get_by_id(session, record_id=custom_script_id)
            if not custom_script:
                raise ResourceNotFoundError(
                resource_name="CustomScript",
                    resource_id=custom_script_id
                )
            if custom_script.workspace_id != workflow.workspace_id:
                raise InvalidInputError(
                    field_name="custom_script_id",
                    message="Custom script does not belong to the same workspace as workflow"
                )
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if script_id is not None:
            update_data["script_id"] = script_id
            update_data["custom_script_id"] = None
        if custom_script_id is not None:
            update_data["custom_script_id"] = custom_script_id
            update_data["script_id"] = None
        if meta_data is not None:
            update_data["meta_data"] = meta_data
        if max_retries is not None:
            update_data["max_retries"] = max_retries
        if timeout_seconds is not None:
            update_data["timeout_seconds"] = timeout_seconds
        
        if update_data:
            cls._node_repo._update(session, record_id=node_id, **update_data)
        
        return cls.get_node(session, node_id=node_id)

    @classmethod
    @with_transaction(manager=None)
    def update_node_input_params(
        cls,
        session,
        *,
        node_id: str,
        input_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Node'un input parametrelerini günceller.
        
        Args:
            node_id: Node ID'si
            input_params: Yeni input parametreleri
            
        Returns:
            Güncellenmiş node bilgileri
        """
        if not isinstance(input_params, dict):
            raise InvalidInputError(
                field_name="input_params",
                message="Input params must be a dictionary"
            )
        
        node = cls._node_repo._get_by_id(session, record_id=node_id)
        
        if not node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=node_id
            )
        
        # Script'i al
        script = None
        if node.script_id:
            script = cls._script_repo._get_by_id(session, record_id=node.script_id)
        elif node.custom_script_id:
            script = cls._custom_script_repo._get_by_id(session, record_id=node.custom_script_id)
        
        if not script:
            raise InvalidInputError(
                field_name="node",
                message="Node has no associated script"
            )
        
        # Validate ve dönüştür
        validated_params = cls._validate_and_convert_frontend_params(
            frontend_params=input_params,
            script_input_schema=script.input_schema or {}
        )
        
        cls._node_repo._update(
            session,
            record_id=node_id,
            input_params=validated_params
        )
        
        return cls.get_node(session, node_id=node_id)

    @classmethod
    @with_transaction(manager=None)
    def sync_input_schema_values(
        cls,
        session,
        *,
        node_id: str,
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Frontend'den gönderilen değerleri input parametrelerine senkronize eder.
        
        Bu fonksiyon:
        - Tüm parametreler için girilen değerleri 'value' alanına atar
        - Değer gönderilmemiş parametreler için 'default_value' değerini 'value' olarak atar
        - Script'in input_schema'sına göre tüm parametreleri oluşturur/günceller
        
        Args:
            node_id: Node ID'si
            values: {param_name: value} formatında gönderilen değerler
            
        Returns:
            Güncellenmiş node bilgileri (input_params dahil)
        """
        if not isinstance(values, dict):
            raise InvalidInputError(
                field_name="values",
                message="Values must be a dictionary"
            )
        
        node = cls._node_repo._get_by_id(session, record_id=node_id)
        
        if not node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=node_id
            )
        
        # Script'i al
        script = None
        if node.script_id:
            script = cls._script_repo._get_by_id(session, record_id=node.script_id)
        elif node.custom_script_id:
            script = cls._custom_script_repo._get_by_id(session, record_id=node.custom_script_id)
        
        if not script:
            raise InvalidInputError(
                field_name="node",
                message="Node has no associated script"
            )
        
        input_schema = script.input_schema or {}
        current_input_params = node.input_params or {}
        synced_params = {}
        
        # Script'in tüm input parametrelerini işle
        for param_name, schema_def in input_schema.items():
            if isinstance(schema_def, str):
                schema_def = {"type": schema_def}
            
            param_type = schema_def.get('type', 'string')
            default_value = schema_def.get('default')
            required = schema_def.get('required', False)
            description = schema_def.get('description')
            
            # Mevcut parametre değerini al
            current_param = current_input_params.get(param_name, {})
            if isinstance(current_param, dict):
                existing_default = current_param.get('default_value', default_value)
            else:
                existing_default = default_value
            
            # Yeni değeri belirle
            new_value = None
            
            # 1. Önce gönderilen values'dan bak
            if param_name in values:
                sent_value = values[param_name]
                # Eğer gönderilen değer dict ise içinden value'yu al
                if isinstance(sent_value, dict):
                    new_value = sent_value.get('value')
                else:
                    new_value = sent_value
            
            # 2. Değer yoksa veya None/boş ise default değeri kullan
            if new_value is None or new_value == '':
                new_value = existing_default
            
            # Required kontrolü
            if required and (new_value is None or new_value == ''):
                raise InvalidInputError(
                    field_name=param_name,
                    message=f"Required parameter '{param_name}' has no value and no default"
                )
            
            # Tip validasyonu (değer varsa)
            if new_value is not None and new_value != '':
                cls._validate_param_type(param_name, new_value, param_type, schema_def)
            
            # Synced parametre oluştur
            synced_params[param_name] = {
                "type": param_type,
                "value": new_value,
                "default_value": existing_default,
                "required": required,
                "description": description
            }
        
        # Node'u güncelle
        cls._node_repo._update(
            session,
            record_id=node_id,
            input_params=synced_params
        )
        
        return cls.get_node(session, node_id=node_id)

    @classmethod
    @with_transaction(manager=None)
    def reset_input_params_to_defaults(
        cls,
        session,
        *,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Node'un input parametrelerini script'in default değerlerine sıfırlar.
        
        Args:
            node_id: Node ID'si
            
        Returns:
            Güncellenmiş node bilgileri
        """
        node = cls._node_repo._get_by_id(session, record_id=node_id)
        
        if not node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=node_id
            )
        
        # Script'i al
        script = None
        if node.script_id:
            script = cls._script_repo._get_by_id(session, record_id=node.script_id)
        elif node.custom_script_id:
            script = cls._custom_script_repo._get_by_id(session, record_id=node.custom_script_id)
        
        if not script:
            raise InvalidInputError(
                field_name="node",
                message="Node has no associated script"
            )
        
        input_schema = script.input_schema or {}
        reset_params = {}
        
        # Script'in tüm input parametrelerini default değerleriyle oluştur
        for param_name, schema_def in input_schema.items():
            if isinstance(schema_def, str):
                schema_def = {"type": schema_def}
            
            param_type = schema_def.get('type', 'string')
            default_value = schema_def.get('default')
            required = schema_def.get('required', False)
            description = schema_def.get('description')
            
            reset_params[param_name] = {
                "type": param_type,
                "value": default_value,  # Default değeri value'ya ata
                "default_value": default_value,
                "required": required,
                "description": description
            }
        
        # Node'u güncelle
        cls._node_repo._update(
            session,
            record_id=node_id,
            input_params=reset_params
        )
        
        return cls.get_node(session, node_id=node_id)

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_node(
        cls,
        session,
        *,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Node'u siler (bağlı edge'ler de silinir).
        
        Args:
            node_id: Node ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        node = cls._node_repo._get_by_id(session, record_id=node_id)
        
        if not node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=node_id
            )
        
        # Bağlı edge'leri sil
        cls._edge_repo._delete_edges_by_node_id(session, node_id=node_id)
        
        # Node'u sil
        cls._node_repo._delete(session, record_id=node_id)
        
        return {
            "success": True,
            "deleted_id": node_id
        }

