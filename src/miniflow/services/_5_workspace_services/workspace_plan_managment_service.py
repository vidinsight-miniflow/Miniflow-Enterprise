from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class WorkspacePlanManagementService:
    """
    Workspace plan yönetim servisi.
    
    Plan upgrade, downgrade, karşılaştırma ve limit yönetimini yönetir.
    NOT: Gerçek ödeme işlemleri Stripe/Paddle webhook'ları ile yapılır.
    """
    _registry = RepositoryRegistry()
    _workspace_repo = _registry.workspace_repository()
    _workspace_plan_repo = _registry.workspace_plans_repository()
    _user_repo = _registry.user_repository()

    # ==================================================================================== PLAN INFO ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_available_plans(
        cls,
        session,
    ) -> Dict[str, Any]:
        """
        Mevcut tüm planları listeler.
        
        Returns:
            {
                "plans": List[Dict],
                "count": int
            }
        """
        plans = cls._workspace_plan_repo._get_all(session)
        
        plan_list = []
        for plan in sorted(plans, key=lambda x: x.display_order):
            plan_list.append({
                "id": plan.id,
                "name": plan.name,
                "display_name": plan.display_name,
                "description": plan.description,
                "is_popular": plan.is_popular,
                "monthly_price_usd": plan.monthly_price_usd,
                "yearly_price_usd": plan.yearly_price_usd,
                "features": plan.features or []
            })
        
        return {
            "plans": plan_list,
            "count": len(plan_list)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_plan_details(
        cls,
        session,
        *,
        plan_id: str,
    ) -> Dict[str, Any]:
        """
        Plan detaylarını getirir.
        
        Args:
            plan_id: Plan ID'si
            
        Returns:
            Plan detayları
        """
        plan = cls._workspace_plan_repo._get_by_id(session, record_id=plan_id)
        
        if not plan:
            raise ResourceNotFoundError(
                resource_name="WorkspacePlan",
                resource_id=plan_id
            )
        
        return {
            "id": plan.id,
            "name": plan.name,
            "display_name": plan.display_name,
            "description": plan.description,
            "is_popular": plan.is_popular,
            "limits": {
                "max_members": plan.max_members_per_workspace,
                "max_workflows": plan.max_workflows_per_workspace,
                "max_custom_scripts": plan.max_custom_scripts_per_workspace,
                "storage_limit_mb": plan.storage_limit_mb_per_workspace,
                "max_file_size_mb": plan.max_file_size_mb_per_workspace,
                "monthly_executions": plan.monthly_execution_limit,
                "max_concurrent_executions": plan.max_concurrent_executions,
                "max_api_keys": plan.max_api_keys_per_workspace
            },
            "features": {
                "custom_scripts": plan.can_use_custom_scripts,
                "api_access": plan.can_use_api_access,
                "webhooks": plan.can_use_webhooks,
                "scheduling": plan.can_use_scheduling,
                "data_export": plan.can_export_data
            },
            "api_limits": {
                "rate_limit_per_minute": plan.api_rate_limit_per_minute,
                "rate_limit_per_hour": plan.api_rate_limit_per_hour,
                "rate_limit_per_day": plan.api_rate_limit_per_day
            },
            "pricing": {
                "monthly_usd": plan.monthly_price_usd,
                "yearly_usd": plan.yearly_price_usd,
                "per_extra_member_usd": plan.price_per_extra_member_usd,
                "per_extra_workflow_usd": plan.price_per_extra_workflow_usd
            },
            "feature_list": plan.features or []
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_current_plan(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace'in mevcut planını getirir.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            Plan ve kullanım bilgileri
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        plan = cls._workspace_plan_repo._get_by_id(session, record_id=workspace.plan_id)
        
        if not plan:
            raise ResourceNotFoundError(
                resource_name="WorkspacePlan",
                resource_id=workspace.plan_id
            )
        
        return {
            "workspace_id": workspace_id,
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "display_name": plan.display_name
            },
            "usage": {
                "members": {
                    "current": workspace.current_member_count,
                    "limit": workspace.member_limit,
                    "percentage": round((workspace.current_member_count / workspace.member_limit) * 100, 1) if workspace.member_limit > 0 else 0
                },
                "workflows": {
                    "current": workspace.current_workflow_count,
                    "limit": workspace.workflow_limit,
                    "percentage": round((workspace.current_workflow_count / workspace.workflow_limit) * 100, 1) if workspace.workflow_limit > 0 else 0
                },
                "storage_mb": {
                    "current": workspace.current_storage_mb,
                    "limit": workspace.storage_limit_mb,
                    "percentage": round((workspace.current_storage_mb / workspace.storage_limit_mb) * 100, 1) if workspace.storage_limit_mb > 0 else 0
                },
                "monthly_executions": {
                    "current": workspace.current_month_executions,
                    "limit": workspace.monthly_execution_limit,
                    "percentage": round((workspace.current_month_executions / workspace.monthly_execution_limit) * 100, 1) if workspace.monthly_execution_limit > 0 else 0
                }
            },
            "billing": {
                "period_start": workspace.current_period_start.isoformat() if workspace.current_period_start else None,
                "period_end": workspace.current_period_end.isoformat() if workspace.current_period_end else None,
                "stripe_subscription_id": workspace.stripe_subscription_id,
                "currency": workspace.billing_currency
            }
        }

    # ==================================================================================== COMPARE ==
    @classmethod
    @with_readonly_session(manager=None)
    def compare_plans(
        cls,
        session,
        *,
        plan_id_1: str,
        plan_id_2: str,
    ) -> Dict[str, Any]:
        """
        İki planı karşılaştırır.
        
        Args:
            plan_id_1: İlk plan ID'si
            plan_id_2: İkinci plan ID'si
            
        Returns:
            Karşılaştırma detayları
        """
        plan1 = cls._workspace_plan_repo._get_by_id(session, record_id=plan_id_1)
        plan2 = cls._workspace_plan_repo._get_by_id(session, record_id=plan_id_2)
        
        if not plan1:
            raise ResourceNotFoundError(
                resource_name="WorkspacePlan",
                resource_id=plan_id_1
            )
        
        if not plan2:
            raise ResourceNotFoundError(
                resource_name="WorkspacePlan",
                resource_id=plan_id_2
            )
        
        def compare_value(val1, val2, higher_is_better=True):
            if val1 == val2:
                return "equal"
            if val1 is None:
                return "plan2_better" if higher_is_better else "plan1_better"
            if val2 is None:
                return "plan1_better" if higher_is_better else "plan2_better"
            if higher_is_better:
                return "plan1_better" if val1 > val2 else "plan2_better"
            return "plan1_better" if val1 < val2 else "plan2_better"
        
        return {
            "plans": {
                "plan1": {"id": plan1.id, "name": plan1.name, "display_name": plan1.display_name},
                "plan2": {"id": plan2.id, "name": plan2.name, "display_name": plan2.display_name}
            },
            "comparison": {
                "max_members": {
                    "plan1": plan1.max_members_per_workspace,
                    "plan2": plan2.max_members_per_workspace,
                    "winner": compare_value(plan1.max_members_per_workspace, plan2.max_members_per_workspace)
                },
                "max_workflows": {
                    "plan1": plan1.max_workflows_per_workspace,
                    "plan2": plan2.max_workflows_per_workspace,
                    "winner": compare_value(plan1.max_workflows_per_workspace, plan2.max_workflows_per_workspace)
                },
                "storage_mb": {
                    "plan1": plan1.storage_limit_mb_per_workspace,
                    "plan2": plan2.storage_limit_mb_per_workspace,
                    "winner": compare_value(plan1.storage_limit_mb_per_workspace, plan2.storage_limit_mb_per_workspace)
                },
                "monthly_executions": {
                    "plan1": plan1.monthly_execution_limit,
                    "plan2": plan2.monthly_execution_limit,
                    "winner": compare_value(plan1.monthly_execution_limit, plan2.monthly_execution_limit)
                },
                "monthly_price_usd": {
                    "plan1": plan1.monthly_price_usd,
                    "plan2": plan2.monthly_price_usd,
                    "winner": compare_value(plan1.monthly_price_usd, plan2.monthly_price_usd, higher_is_better=False)
                }
            },
            "features": {
                "custom_scripts": {"plan1": plan1.can_use_custom_scripts, "plan2": plan2.can_use_custom_scripts},
                "api_access": {"plan1": plan1.can_use_api_access, "plan2": plan2.can_use_api_access},
                "webhooks": {"plan1": plan1.can_use_webhooks, "plan2": plan2.can_use_webhooks},
                "scheduling": {"plan1": plan1.can_use_scheduling, "plan2": plan2.can_use_scheduling},
                "data_export": {"plan1": plan1.can_export_data, "plan2": plan2.can_export_data}
            }
        }

    # ==================================================================================== UPGRADE/DOWNGRADE ==
    @classmethod
    @with_readonly_session(manager=None)
    def check_upgrade_eligibility(
        cls,
        session,
        *,
        workspace_id: str,
        target_plan_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace'in belirtilen plana upgrade yapıp yapamayacağını kontrol eder.
        
        Args:
            workspace_id: Workspace ID'si
            target_plan_id: Hedef plan ID'si
            
        Returns:
            {
                "eligible": bool,
                "is_upgrade": bool,
                "current_plan": Dict,
                "target_plan": Dict,
                "price_difference": float
            }
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        current_plan = cls._workspace_plan_repo._get_by_id(session, record_id=workspace.plan_id)
        target_plan = cls._workspace_plan_repo._get_by_id(session, record_id=target_plan_id)
        
        if not current_plan:
            raise ResourceNotFoundError(
                resource_name="WorkspacePlan",
                resource_id=workspace.plan_id
            )
        
        if not target_plan:
            raise ResourceNotFoundError(
                resource_name="WorkspacePlan",
                resource_id=target_plan_id
            )
        
        # Aynı plan mı?
        if current_plan.id == target_plan.id:
            raise BusinessRuleViolationError(
                rule_name="same_plan",
                message="Workspace is already on this plan"
            )
        
        # Upgrade mi downgrade mi?
        is_upgrade = target_plan.monthly_price_usd > current_plan.monthly_price_usd
        price_difference = target_plan.monthly_price_usd - current_plan.monthly_price_usd
        
        # Downgrade kontrolü: Mevcut kullanım hedef plan limitlerini aşıyor mu?
        issues = []
        if not is_upgrade:
            if workspace.current_member_count > target_plan.max_members_per_workspace:
                issues.append(f"Current members ({workspace.current_member_count}) exceeds target plan limit ({target_plan.max_members_per_workspace})")
            if workspace.current_workflow_count > target_plan.max_workflows_per_workspace:
                issues.append(f"Current workflows ({workspace.current_workflow_count}) exceeds target plan limit ({target_plan.max_workflows_per_workspace})")
            if workspace.current_storage_mb > target_plan.storage_limit_mb_per_workspace:
                issues.append(f"Current storage ({workspace.current_storage_mb}MB) exceeds target plan limit ({target_plan.storage_limit_mb_per_workspace}MB)")
        
        return {
            "eligible": len(issues) == 0,
            "is_upgrade": is_upgrade,
            "current_plan": {
                "id": current_plan.id,
                "name": current_plan.name,
                "monthly_price_usd": current_plan.monthly_price_usd
            },
            "target_plan": {
                "id": target_plan.id,
                "name": target_plan.name,
                "monthly_price_usd": target_plan.monthly_price_usd
            },
            "price_difference_monthly": price_difference,
            "issues": issues if issues else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def check_downgrade_eligibility(
        cls,
        session,
        *,
        workspace_id: str,
        target_plan_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace'in belirtilen plana downgrade yapıp yapamayacağını kontrol eder.
        
        Downgrade için mevcut kullanımın hedef plan limitlerinin altında olması gerekir.
        
        Args:
            workspace_id: Workspace ID'si
            target_plan_id: Hedef plan ID'si
            
        Returns:
            {
                "eligible": bool,
                "blocking_resources": List[Dict] (limit aşan kaynaklar)
            }
        """
        result = cls.check_upgrade_eligibility(session, workspace_id=workspace_id, target_plan_id=target_plan_id)
        
        if result["is_upgrade"]:
            raise BusinessRuleViolationError(
                rule_name="not_downgrade",
                message="Target plan is more expensive than current plan. This is an upgrade, not downgrade."
            )
        
        return {
            "eligible": result["eligible"],
            "blocking_issues": result.get("issues"),
            "current_plan": result["current_plan"],
            "target_plan": result["target_plan"],
            "monthly_savings": abs(result["price_difference_monthly"])
        }

    @classmethod
    @with_transaction(manager=None)
    def upgrade_plan(
        cls,
        session,
        *,
        workspace_id: str,
        target_plan_id: str,
        stripe_subscription_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workspace planını upgrade eder.
        
        NOT: Gerçek ödeme işlemi Stripe webhook ile yapılmalıdır.
        Bu metod sadece veritabanını günceller.
        
        Args:
            workspace_id: Workspace ID'si
            target_plan_id: Hedef plan ID'si
            stripe_subscription_id: Stripe subscription ID (opsiyonel)
            
        Returns:
            Upgrade sonucu
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        target_plan = cls._workspace_plan_repo._get_by_id(session, record_id=target_plan_id)
        
        if not target_plan:
            raise ResourceNotFoundError(
                resource_name="WorkspacePlan",
                resource_id=target_plan_id
            )
        
        # Owner'ın free workspace sayısını güncelle (eğer free'den ücretliye geçiyorsa)
        user = cls._user_repo._get_by_id(session, record_id=workspace.owner_id)
        current_plan = cls._workspace_plan_repo._get_by_id(session, record_id=workspace.plan_id)
        
        if user and current_plan:
            # Freemium'dan ücretliye geçiş
            if current_plan.name == "Freemium" and target_plan.name != "Freemium":
                cls._user_repo._update(
                    session,
                    record_id=workspace.owner_id,
                    current_free_workspace_count=max(0, user.current_free_workspace_count - 1)
                )
        
        # Workspace'i güncelle
        cls._workspace_repo._update(
            session,
            record_id=workspace_id,
            plan_id=target_plan.id,
            member_limit=target_plan.max_members_per_workspace,
            workflow_limit=target_plan.max_workflows_per_workspace,
            custom_script_limit=target_plan.max_custom_scripts_per_workspace or 0,
            max_file_size_mb_per_workspace=target_plan.max_file_size_mb_per_workspace,
            storage_limit_mb=target_plan.storage_limit_mb_per_workspace,
            api_key_limit=target_plan.max_api_keys_per_workspace or 0,
            monthly_execution_limit=target_plan.monthly_execution_limit,
            monthly_concurrent_executions=target_plan.max_concurrent_executions,
            stripe_subscription_id=stripe_subscription_id if stripe_subscription_id else workspace.stripe_subscription_id
        )
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "new_plan_id": target_plan.id,
            "new_plan_name": target_plan.name,
            "upgraded_at": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    @with_transaction(manager=None)
    def downgrade_plan(
        cls,
        session,
        *,
        workspace_id: str,
        target_plan_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace planını downgrade eder.
        
        NOT: Downgrade genellikle billing period sonunda uygulanır.
        
        Args:
            workspace_id: Workspace ID'si
            target_plan_id: Hedef plan ID'si
            
        Returns:
            Downgrade sonucu
        """
        # Eligibility kontrolü
        eligibility = cls.check_downgrade_eligibility(
            session, 
            workspace_id=workspace_id, 
            target_plan_id=target_plan_id
        )
        
        if not eligibility["eligible"]:
            raise BusinessRuleViolationError(
                rule_name="downgrade_blocked",
                message=f"Cannot downgrade: {'; '.join(eligibility['blocking_issues'])}"
            )
        
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        target_plan = cls._workspace_plan_repo._get_by_id(session, record_id=target_plan_id)
        
        # Owner'ın free workspace sayısını güncelle (eğer ücretliden free'ye geçiyorsa)
        user = cls._user_repo._get_by_id(session, record_id=workspace.owner_id)
        current_plan = cls._workspace_plan_repo._get_by_id(session, record_id=workspace.plan_id)
        
        if user and current_plan:
            # Ücretliden Freemium'a geçiş
            if current_plan.name != "Freemium" and target_plan.name == "Freemium":
                # Free workspace limiti kontrolü
                if user.current_free_workspace_count >= 1:
                    raise BusinessRuleViolationError(
                        rule_name="free_workspace_limit",
                        message="You already have a free workspace. Cannot downgrade to Freemium."
                    )
                cls._user_repo._update(
                    session,
                    record_id=workspace.owner_id,
                    current_free_workspace_count=user.current_free_workspace_count + 1
                )
        
        # Workspace'i güncelle
        cls._workspace_repo._update(
            session,
            record_id=workspace_id,
            plan_id=target_plan.id,
            member_limit=target_plan.max_members_per_workspace,
            workflow_limit=target_plan.max_workflows_per_workspace,
            custom_script_limit=target_plan.max_custom_scripts_per_workspace or 0,
            max_file_size_mb_per_workspace=target_plan.max_file_size_mb_per_workspace,
            storage_limit_mb=target_plan.storage_limit_mb_per_workspace,
            api_key_limit=target_plan.max_api_keys_per_workspace or 0,
            monthly_execution_limit=target_plan.monthly_execution_limit,
            monthly_concurrent_executions=target_plan.max_concurrent_executions
        )
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "new_plan_id": target_plan.id,
            "new_plan_name": target_plan.name,
            "downgraded_at": datetime.now(timezone.utc).isoformat()
        }

    # ==================================================================================== BILLING ==
    @classmethod
    @with_transaction(manager=None)
    def update_billing_info(
        cls,
        session,
        *,
        workspace_id: str,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        billing_email: Optional[str] = None,
        billing_currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workspace billing bilgilerini günceller.
        
        Args:
            workspace_id: Workspace ID'si
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            billing_email: Fatura email adresi
            billing_currency: Para birimi (USD, EUR, vb.)
            
        Returns:
            Güncellenmiş billing bilgileri
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        update_data = {}
        if stripe_customer_id is not None:
            update_data["stripe_customer_id"] = stripe_customer_id
        if stripe_subscription_id is not None:
            update_data["stripe_subscription_id"] = stripe_subscription_id
        if billing_email is not None:
            update_data["billing_email"] = billing_email
        if billing_currency is not None:
            update_data["billing_currency"] = billing_currency
        
        if update_data:
            cls._workspace_repo._update(session, record_id=workspace_id, **update_data)
        
        # Güncel bilgileri al
        updated_workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "stripe_customer_id": updated_workspace.stripe_customer_id,
            "stripe_subscription_id": updated_workspace.stripe_subscription_id,
            "billing_email": updated_workspace.billing_email,
            "billing_currency": updated_workspace.billing_currency
        }

    @classmethod
    @with_transaction(manager=None)
    def update_billing_period(
        cls,
        session,
        *,
        workspace_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """
        Billing dönemini günceller ve aylık sayaçları sıfırlar.
        
        NOT: Genellikle Stripe webhook'u tarafından çağrılır.
        
        Args:
            workspace_id: Workspace ID'si
            period_start: Dönem başlangıcı
            period_end: Dönem bitişi
            
        Returns:
            {"success": True}
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Billing dönemini güncelle
        cls._workspace_repo._update(
            session,
            record_id=workspace_id,
            current_period_start=period_start,
            current_period_end=period_end
        )
        
        # Aylık sayaçları sıfırla
        cls._workspace_repo._reset_monthly_counters(session, workspace_id=workspace_id)
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        }

    # ==================================================================================== LIMIT CHECKS ==
    @classmethod
    @with_readonly_session(manager=None)
    def check_limit(
        cls,
        session,
        *,
        workspace_id: str,
        limit_type: str,
        increment: int = 1,
    ) -> Dict[str, Any]:
        """
        Belirtilen limit tipinin aşılıp aşılmayacağını kontrol eder.
        
        Args:
            workspace_id: Workspace ID'si
            limit_type: Limit tipi (members, workflows, storage, executions, api_keys, scripts)
            increment: Artış miktarı
            
        Returns:
            {
                "allowed": bool,
                "current": int,
                "limit": int,
                "would_exceed_by": int (eğer limit aşılıyorsa)
            }
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        limit_map = {
            "members": (workspace.current_member_count, workspace.member_limit),
            "workflows": (workspace.current_workflow_count, workspace.workflow_limit),
            "storage": (workspace.current_storage_mb, workspace.storage_limit_mb),
            "executions": (workspace.current_month_executions, workspace.monthly_execution_limit),
            "api_keys": (workspace.current_api_key_count, workspace.api_key_limit),
            "scripts": (workspace.current_custom_script_count, workspace.custom_script_limit),
        }
        
        if limit_type not in limit_map:
            raise BusinessRuleViolationError(
                rule_name="invalid_limit_type",
                message=f"Invalid limit type: {limit_type}. Valid types: {', '.join(limit_map.keys())}"
            )
        
        current, limit = limit_map[limit_type]
        new_value = current + increment
        allowed = new_value <= limit if limit > 0 else True  # -1 = unlimited
        
        result = {
            "allowed": allowed,
            "current": current,
            "limit": limit,
            "after_increment": new_value
        }
        
        if not allowed:
            result["would_exceed_by"] = new_value - limit
        
        return result

