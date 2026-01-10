USER_ROLES_SEED = [
    {   
        # Base
        "name": "Owner",
        "description": "Workspace owner with full permissions including deletion and billing",

        # Workspace permissions
        "can_view_workspace": True,
        "can_edit_workspace": True,
        "can_delete_workspace": True,
        "can_invite_members": True,
        "can_remove_members": True,
        "can_change_plan": True,

        # Workflow permissions
        "can_view_workflows": True,
        "can_create_workflows": True,
        "can_edit_workflows": True,
        "can_delete_workflows": True,
        "can_execute_workflows": True,
        "can_share_workflows": True,
        
        # Credential permissions
        "can_view_credentials": True,
        "can_create_credentials": True,
        "can_edit_credentials": True,
        "can_delete_credentials": True,
        "can_share_credentials": True,
        "can_view_credential_values": True,
        
        # File permissions
        "can_view_files": True,
        "can_upload_files": True,
        "can_download_files": True,
        "can_delete_files": True,
        "can_share_files": True,
        
        # Database permissions
        "can_view_databases": True,
        "can_create_databases": True,
        "can_edit_databases": True,
        "can_delete_databases": True,
        "can_share_databases": True,
        "can_view_connection_details": True,
        
        # Variable permissions
        "can_view_variables": True,
        "can_create_variables": True,
        "can_edit_variables": True,
        "can_delete_variables": True,
        "can_share_variables": True,
        "can_view_variable_values": True,
        
        # API Key permissions
        "can_view_api_keys": True,
        "can_create_api_keys": True,
        "can_edit_api_keys": True,
        "can_delete_api_keys": True,
        "can_share_api_keys": True,
        "can_view_api_key_values": True,

        # System
        "is_system_role": True,
        "display_order": 1,
    },
    {
        # Base
        "name": "Admin",
        "description": "Administrator with management permissions except workspace deletion and billing",

        # Workspace permissions
        "can_view_workspace": True,
        "can_edit_workspace": True,
        "can_delete_workspace": True,
        "can_invite_members": True,
        "can_remove_members": True,
        "can_change_plan": False,

        # Workflow permissions
        "can_view_workflows": True,
        "can_create_workflows": True,
        "can_edit_workflows": True,
        "can_delete_workflows": True,
        "can_execute_workflows": True,
        "can_share_workflows": True,
        
        # Credential permissions
        "can_view_credentials": True,
        "can_create_credentials": True,
        "can_edit_credentials": True,
        "can_delete_credentials": True,
        "can_share_credentials": True,
        "can_view_credential_values": True,
        
        # File permissions
        "can_view_files": True,
        "can_upload_files": True,
        "can_download_files": True,
        "can_delete_files": True,
        "can_share_files": True,
        
        # Database permissions
        "can_view_databases": True,
        "can_create_databases": True,
        "can_edit_databases": True,
        "can_delete_databases": True,
        "can_share_databases": True,
        "can_view_connection_details": True,
        
        # Variable permissions
        "can_view_variables": True,
        "can_create_variables": True,
        "can_edit_variables": True,
        "can_delete_variables": True,
        "can_share_variables": True,
        "can_view_variable_values": True,
        
        # API Key permissions
        "can_view_api_keys": True,
        "can_create_api_keys": True,
        "can_edit_api_keys": True,
        "can_delete_api_keys": True,
        "can_share_api_keys": True,
        "can_view_api_key_values": True,

        # System
        "is_system_role": True,
        "display_order": 2,
    },
    {
# Base
        "name": "Editor",
        "description": "Editor with content creation and modification permissions",

        # Workspace permissions
        "can_view_workspace": True,
        "can_edit_workspace": False,
        "can_delete_workspace": False,
        "can_invite_members": False,
        "can_remove_members": False,
        "can_change_plan": False,

        # Workflow permissions
        "can_view_workflows": True,
        "can_create_workflows": True,
        "can_edit_workflows": True,
        "can_delete_workflows": True,
        "can_execute_workflows": True,
        "can_share_workflows": False,
        
        # Credential permissions
        "can_view_credentials": True,
        "can_create_credentials": True,
        "can_edit_credentials": True,
        "can_delete_credentials": True,
        "can_share_credentials": False,
        "can_view_credential_values": False,
        
        # File permissions
        "can_view_files": True,
        "can_upload_files": True,
        "can_download_files": True,
        "can_delete_files": True,
        "can_share_files": False,
        
        # Database permissions
        "can_view_databases": True,
        "can_create_databases": True,
        "can_edit_databases": True,
        "can_delete_databases": True,
        "can_share_databases": False,
        "can_view_connection_details": False,
        
        # Variable permissions
        "can_view_variables": True,
        "can_create_variables": True,
        "can_edit_variables": True,
        "can_delete_variables": True,
        "can_share_variables": False,
        "can_view_variable_values": True,
        
        # API Key permissions
        "can_view_api_keys": True,
        "can_create_api_keys": True,
        "can_edit_api_keys": True,
        "can_delete_api_keys": True,
        "can_share_api_keys": False,
        "can_view_api_key_values": True,

        # System
        "is_system_role": True,
        "display_order": 3,
    },
    {
# Base
        "name": "Viewer",
        "description": "Viewer with read-only access and workflow execution",

        # Workspace permissions
        "can_view_workspace": True,
        "can_edit_workspace": False,
        "can_delete_workspace": False,
        "can_invite_members": False,
        "can_remove_members": False,
        "can_change_plan": False,

        # Workflow permissions
        "can_view_workflows": True,
        "can_create_workflows": False,
        "can_edit_workflows": False,
        "can_delete_workflows": False,
        "can_execute_workflows": False,
        "can_share_workflows": False,
        
        # Credential permissions
        "can_view_credentials": False,
        "can_create_credentials": False,
        "can_edit_credentials": False,
        "can_delete_credentials": False,
        "can_share_credentials": False,
        "can_view_credential_values": False,
        
        # File permissions
        "can_view_files": True,
        "can_upload_files": False,
        "can_download_files": False,
        "can_delete_files": False,
        "can_share_files": False,
        
        # Database permissions
        "can_view_databases": True,
        "can_create_databases": False,
        "can_edit_databases": False,
        "can_delete_databases": False,
        "can_share_databases": False,
        "can_view_connection_details": False,
        
        # Variable permissions
        "can_view_variables": True,
        "can_create_variables": False,
        "can_edit_variables": False,
        "can_delete_variables": False,
        "can_share_variables": False,
        "can_view_variable_values": False,
        
        # API Key permissions
        "can_view_api_keys": False,
        "can_create_api_keys": False,
        "can_edit_api_keys": False,
        "can_delete_api_keys": False,
        "can_share_api_keys": False,
        "can_view_api_key_values": False,

        # System
        "is_system_role": True,
        "display_order": 4,
    }
]