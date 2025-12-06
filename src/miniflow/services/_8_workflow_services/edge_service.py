from typing import Optional, Dict, Any, List

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)


class EdgeService:
    """
    Workflow Edge yönetim servisi.
    
    Node'lar arası bağlantıların (edge) CRUD işlemlerini sağlar.
    NOT: workflow_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _edge_repo = _registry.edge_repository()
    _workflow_repo = _registry.workflow_repository()
    _node_repo = _registry.node_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_edge(
        cls,
        session,
        *,
        workflow_id: str,
        from_node_id: str,
        to_node_id: str,
        created_by: str,
    ) -> Dict[str, Any]:
        """
        Yeni edge oluşturur (iki node arasında bağlantı).
        
        - Self-loop kontrolü yapılır (from_node_id != to_node_id)
        - Her iki node da aynı workflow'a ait olmalı
        - Aynı node'lar arasında birden fazla edge olamaz
        
        Args:
            workflow_id: Workflow ID'si
            from_node_id: Başlangıç node ID'si
            to_node_id: Hedef node ID'si
            created_by: Oluşturan kullanıcı ID'si
            
        Returns:
            {"id": str}
        """
        # Self-loop kontrolü
        if from_node_id == to_node_id:
            raise InvalidInputError(
                field_name="edge",
                message="Edge cannot connect a node to itself"
            )
        
        # Workflow kontrolü
        workflow = cls._workflow_repo._get_by_id(session, record_id=workflow_id)
        if not workflow:
            raise ResourceNotFoundError(
                resource_name="Workflow",
                resource_id=workflow_id
            )
        
        # From node kontrolü
        from_node = cls._node_repo._get_by_id(session, record_id=from_node_id)
        if not from_node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=from_node_id
            )
        if from_node.workflow_id != workflow_id:
            raise InvalidInputError(
                field_name="from_node_id",
                message="From node does not belong to this workflow"
            )
        
        # To node kontrolü
        to_node = cls._node_repo._get_by_id(session, record_id=to_node_id)
        if not to_node:
            raise ResourceNotFoundError(
                resource_name="Node",
                resource_id=to_node_id
            )
        if to_node.workflow_id != workflow_id:
            raise InvalidInputError(
                field_name="to_node_id",
                message="To node does not belong to this workflow"
            )
        
        # Benzersizlik kontrolü
        existing = cls._edge_repo._get_by_nodes(
            session,
            workflow_id=workflow_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Edge",
                conflicting_field="from_node_id->to_node_id",
                message=f"Edge from node {from_node_id} to node {to_node_id} already exists in workflow {workflow_id}"
            )
        
        # Edge oluştur
        edge = cls._edge_repo._create(
            session,
            workflow_id=workflow_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            created_by=created_by
        )
        
        return {"id": edge.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_edge(
        cls,
        session,
        *,
        edge_id: str,
    ) -> Dict[str, Any]:
        """
        Edge detaylarını getirir.
        
        Args:
            edge_id: Edge ID'si
            
        Returns:
            Edge detayları
        """
        edge = cls._edge_repo._get_by_id(session, record_id=edge_id)
        
        if not edge:
            raise ResourceNotFoundError(
                resource_name="Edge",
                resource_id=edge_id
            )
        
        return {
            "id": edge.id,
            "workflow_id": edge.workflow_id,
            "from_node_id": edge.from_node_id,
            "to_node_id": edge.to_node_id,
            "created_at": edge.created_at.isoformat() if edge.created_at else None,
            "updated_at": edge.updated_at.isoformat() if edge.updated_at else None,
            "created_by": edge.created_by
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workflow_edges(
        cls,
        session,
        *,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Workflow'un edge'lerini listeler.
        
        Args:
            workflow_id: Workflow ID'si
            
        Returns:
            {"workflow_id": str, "edges": List[Dict], "count": int}
        """
        edges = cls._edge_repo._get_all_by_workflow_id(session, workflow_id=workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "edges": [
                {
                    "id": e.id,
                    "from_node_id": e.from_node_id,
                    "to_node_id": e.to_node_id
                }
                for e in edges
            ],
            "count": len(edges)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_outgoing_edges(
        cls,
        session,
        *,
        workflow_id: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Bir node'dan çıkan edge'leri listeler.
        
        Args:
            workflow_id: Workflow ID'si
            node_id: Node ID'si
            
        Returns:
            {"node_id": str, "edges": List[Dict], "count": int}
        """
        edges = cls._edge_repo._get_by_from_node_id(
            session,
            workflow_id=workflow_id,
            from_node_id=node_id
        )
        
        return {
            "node_id": node_id,
            "edges": [
                {
                    "id": e.id,
                    "to_node_id": e.to_node_id
                }
                for e in edges
            ],
            "count": len(edges)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_incoming_edges(
        cls,
        session,
        *,
        workflow_id: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Bir node'a giren edge'leri listeler.
        
        Args:
            workflow_id: Workflow ID'si
            node_id: Node ID'si
            
        Returns:
            {"node_id": str, "edges": List[Dict], "count": int}
        """
        edges = cls._edge_repo._get_by_to_node_id(
            session,
            workflow_id=workflow_id,
            to_node_id=node_id
        )
        
        return {
            "node_id": node_id,
            "edges": [
                {
                    "id": e.id,
                    "from_node_id": e.from_node_id
                }
                for e in edges
            ],
            "count": len(edges)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_edge(
        cls,
        session,
        *,
        edge_id: str,
        from_node_id: Optional[str] = None,
        to_node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Edge'i günceller (node bağlantılarını değiştirir).
        
        Args:
            edge_id: Edge ID'si
            from_node_id: Yeni başlangıç node ID (opsiyonel)
            to_node_id: Yeni hedef node ID (opsiyonel)
            
        Returns:
            Güncellenmiş edge bilgileri
        """
        edge = cls._edge_repo._get_by_id(session, record_id=edge_id)
        
        if not edge:
            raise ResourceNotFoundError(
                resource_name="Edge",
                resource_id=edge_id
            )
        
        new_from_node_id = from_node_id if from_node_id is not None else edge.from_node_id
        new_to_node_id = to_node_id if to_node_id is not None else edge.to_node_id
        
        # Self-loop kontrolü
        if new_from_node_id == new_to_node_id:
            raise InvalidInputError(
                field_name="edge",
                message="Edge cannot connect a node to itself"
            )
        
        # Node kontrolleri
        if from_node_id is not None and from_node_id != edge.from_node_id:
            from_node = cls._node_repo._get_by_id(session, record_id=from_node_id)
            if not from_node:
                raise ResourceNotFoundError(
                resource_name="Node",
                    resource_id=from_node_id
                )
            if from_node.workflow_id != edge.workflow_id:
                raise InvalidInputError(
                    field_name="from_node_id",
                    message="From node does not belong to this workflow"
                )
        
        if to_node_id is not None and to_node_id != edge.to_node_id:
            to_node = cls._node_repo._get_by_id(session, record_id=to_node_id)
            if not to_node:
                raise ResourceNotFoundError(
                resource_name="Node",
                    resource_id=to_node_id
                )
            if to_node.workflow_id != edge.workflow_id:
                raise InvalidInputError(
                    field_name="to_node_id",
                    message="To node does not belong to this workflow"
                )
        
        # Benzersizlik kontrolü (değişiklik varsa)
        if from_node_id is not None or to_node_id is not None:
            existing = cls._edge_repo._get_by_nodes(
                session,
                workflow_id=edge.workflow_id,
                from_node_id=new_from_node_id,
                to_node_id=new_to_node_id
            )
            if existing and existing.id != edge_id:
                raise ResourceAlreadyExistsError(
                    resource_name="Edge",
                    conflicting_field="from_node_id->to_node_id",
                    message=f"Edge from node {new_from_node_id} to node {new_to_node_id} already exists in workflow {workflow_id}"
                )
        
        update_data = {}
        if from_node_id is not None:
            update_data["from_node_id"] = from_node_id
        if to_node_id is not None:
            update_data["to_node_id"] = to_node_id
        
        if update_data:
            cls._edge_repo._update(session, record_id=edge_id, **update_data)
        
        return cls.get_edge(session, edge_id=edge_id)

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_edge(
        cls,
        session,
        *,
        edge_id: str,
    ) -> Dict[str, Any]:
        """
        Edge'i siler.
        
        Args:
            edge_id: Edge ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        edge = cls._edge_repo._get_by_id(session, record_id=edge_id)
        
        if not edge:
            raise ResourceNotFoundError(
                resource_name="Edge",
                resource_id=edge_id
            )
        
        cls._edge_repo._delete(session, record_id=edge_id)
        
        return {
            "success": True,
            "deleted_id": edge_id
        }

