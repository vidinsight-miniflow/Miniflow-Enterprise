WORKSPACE_PLANS_SEED = [
    {
        "name": "Freemium",
        "display_name": "Free Plan",
        "description": "Perfect for individuals and small projects",
        "display_order": 0,
        "is_popular": False,
        
        # Limits
        "max_members_per_workspace": 1,
        "max_workflows_per_workspace": 3,
        "max_custom_scripts_per_workspace": 0,
        "storage_limit_mb_per_workspace": 100,
        "max_file_size_mb_per_workspace": 5,

        # Monthly Limits
        "monthly_execution_limit": 100,
        "max_concurrent_executions": 1,
        
        # Features
        "can_use_custom_scripts": False,
        "can_use_api_access": False,
        "can_use_webhooks": False,
        "can_use_scheduling": False,
        "can_export_data": False,
        
        # API Access
        "max_api_keys_per_workspace": 0,
        "api_rate_limit_per_minute": 10,
        "api_rate_limit_per_hour": 100,
        "api_rate_limit_per_day": 1000,
        
        # Pricing
        "monthly_price_usd": 0.0,
        "yearly_price_usd": 0.0,
        "price_per_extra_member_usd": 0.0,
        "price_per_extra_workflow_usd": 0.0,
        
        # Features list
        "features": [
            "1 workspace member",
            "3 workflows",
            "100 MB storage",
            "100 executions/month",
            "Community support"
        ]
    },
    {
        "name": "Starter",
        "display_name": "Starter Plan",
        "description": "Great for small teams getting started",
        "display_order": 1,
        "is_popular": False,
        
        # Limits
        "max_members_per_workspace": 5,
        "max_workflows_per_workspace": 25,
        "max_custom_scripts_per_workspace": 10,
        "storage_limit_mb_per_workspace": 1024,  # 1 GB
        "max_file_size_mb_per_workspace": 25,

        # Monthly Limits
        "monthly_execution_limit": 2000,
        "max_concurrent_executions": 3,
        
        # Features
        "can_use_custom_scripts": True,
        "can_use_api_access": True,
        "can_use_webhooks": True,
        "can_use_scheduling": True,
        "can_export_data": True,
        
        # API Access
        "max_api_keys_per_workspace": 5,
        "api_rate_limit_per_minute": 60,
        "api_rate_limit_per_hour": 1000,
        "api_rate_limit_per_day": 10000,
        
        # Pricing
        "monthly_price_usd": 29.0,
        "yearly_price_usd": 290.0,  # ~2 months free
        "price_per_extra_member_usd": 5.0,
        "price_per_extra_workflow_usd": 2.0,
        
        # Features list
        "features": [
            "5 workspace members",
            "25 workflows",
            "1 GB storage",
            "2,000 executions/month",
            "Custom scripts",
            "API access",
            "Webhooks",
            "Scheduling",
            "Data export",
        ]
    },
    {
        "name": "Professional",
        "display_name": "Professional Plan",
        "description": "Best for growing teams and businesses",
        "display_order": 2,
        "is_popular": True,
        
        # Limits
        "max_members_per_workspace": 15,
        "max_workflows_per_workspace": 100,
        "max_custom_scripts_per_workspace": 50,
        "storage_limit_mb_per_workspace": 10240,  # 10 GB
        "max_file_size_mb_per_workspace": 100,

        # Monthly Limits
        "monthly_execution_limit": 10000,
        "max_concurrent_executions": 10,
        
        # Features
        "can_use_custom_scripts": True,
        "can_use_api_access": True,
        "can_use_webhooks": True,
        "can_use_scheduling": True,
        "can_export_data": True,
        
        # API Access
        "max_api_keys_per_workspace": 25,
        "api_rate_limit_per_minute": 300,
        "api_rate_limit_per_hour": 10000,
        "api_rate_limit_per_day": 100000,
        
        # Pricing
        "monthly_price_usd": 99.0,
        "yearly_price_usd": 990.0,  # ~2 months free
        "price_per_extra_member_usd": 8.0,
        "price_per_extra_workflow_usd": 5.0,
        
        # Features list
        "features": [
            "15 workspace members",
            "100 workflows",
            "10 GB storage",
            "10,000 executions/month",
            "Custom scripts",
            "API access",
            "Webhooks",
            "Scheduling",
            "Data export",
            "Priority support",
            "Advanced analytics"
        ]
    },
    {
        "name": "Business",
        "display_name": "Business Plan",
        "description": "Advanced features for larger organizations",
        "display_order": 3,
        "is_popular": False,
        
        # Limits
        "max_members_per_workspace": 50,
        "max_workflows_per_workspace": 500,
        "max_custom_scripts_per_workspace": 200,
        "storage_limit_mb_per_workspace": 51200,  # 50 GB
        "max_file_size_mb_per_workspace": 500,

        # Monthly Limits
        "monthly_execution_limit": 50000,
        "max_concurrent_executions": 25,
        
        # Features
        "can_use_custom_scripts": True,
        "can_use_api_access": True,
        "can_use_webhooks": True,
        "can_use_scheduling": True,
        "can_export_data": True,
        
        # API Access
        "max_api_keys_per_workspace": 100,
        "api_rate_limit_per_minute": 1000,
        "api_rate_limit_per_hour": 50000,
        "api_rate_limit_per_day": 500000,
        
        # Pricing
        "monthly_price_usd": 299.0,
        "yearly_price_usd": 2990.0,  # ~2 months free
        "price_per_extra_member_usd": 10.0,
        "price_per_extra_workflow_usd": 8.0,
        
        # Features list
        "features": [
            "50 workspace members",
            "500 workflows",
            "50 GB storage",
            "50,000 executions/month",
            "Unlimited custom scripts",
            "API access",
            "Webhooks",
            "Scheduling",
            "Data export",
            "Priority support",
            "Advanced analytics",
            "SLA guarantee",
            "Dedicated account manager"
        ]
    }
]