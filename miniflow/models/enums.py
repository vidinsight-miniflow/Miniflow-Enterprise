"""
DATABASE ENUMS - Veritabanı Modelleri İçin Enum Tanımları
=========================================================

Amaç:
    - Tüm veritabanı modellerinde kullanılan enum tiplerini merkezi bir yerde tanımlar
    - Type safety ve code consistency sağlar
    - Veri bütünlüğünü korur

Kullanım:
    from database.models.enums import WorkflowStatus, ExecutionStatus
    
    # Model içinde
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)

Not:
    - Tüm enum'lar string bazlıdır (str, Enum)
    - Veritabanında enum value (string) olarak saklanır
    - Python 3.11+ StrEnum kullanmak idealdir ama 3.10 uyumluluk için str, Enum kullanılır
"""

import enum
from enum import Enum


# ============================================================================
# SUBSCRIPTION & BILLING ENUMS
# ============================================================================

class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "ACTIVE"               # Subscription is active
    PAST_DUE = "PAST_DUE"          # Payment failed, grace period
    CANCELLED = "CANCELLED"         # Subscription cancelled by user
    EXPIRED = "EXPIRED"             # Trial or subscription expired
    PAUSED = "PAUSED"               # Subscription paused by user
    INCOMPLETE = "INCOMPLETE"       # Initial payment incomplete
    UNPAID = "UNPAID"               # Payment failed, suspended


class InvoiceStatus(str, Enum):
    """Invoice status"""
    PENDING = "PENDING"         # Invoice created, awaiting payment
    PAID = "PAID"               # Payment received
    OVERDUE = "OVERDUE"         # Payment past due date
    CANCELLED = "CANCELLED"     # Invoice cancelled
    REFUNDED = "REFUNDED"       # Payment refunded
    VOID = "VOID"               # Invoice voided


class InvitationStatus(str, Enum):
    """Workspace invitation status"""
    PENDING = "PENDING"         # Invitation sent, awaiting response
    ACCEPTED = "ACCEPTED"       # Invitation accepted
    DECLINED = "DECLINED"       # Invitation declined by invitee
    EXPIRED = "EXPIRED"         # Invitation token expired
    CANCELLED = "CANCELLED"     # Invitation cancelled by inviter


# ============================================================================
# WORKFLOW & EXECUTION ENUMS
# ============================================================================

class WorkflowStatus(str, Enum):
    """Workflow status"""
    DRAFT = "DRAFT"             # Workflow being created/edited
    ACTIVE = "ACTIVE"           # Workflow active and can be executed
    DEACTIVATED = "DEACTIVATED" # Workflow temporarily disabled
    ARCHIVED = "ARCHIVED"       # Workflow archived (read-only)


class ExecutionStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "PENDING"         # Execution queued
    RUNNING = "RUNNING"         # Execution in progress
    COMPLETED = "COMPLETED"     # Execution finished successfully
    FAILED = "FAILED"           # Execution failed with error
    CANCELLED = "CANCELLED"     # Execution cancelled by user
    TIMEOUT = "TIMEOUT"         # Execution exceeded timeout limit


class TriggerType(str, Enum):
    """Workflow trigger types"""
    MANUAL = "MANUAL"           # Manual trigger by user
    SCHEDULED = "SCHEDULED"     # Scheduled trigger (cron)
    WEBHOOK = "WEBHOOK"         # HTTP webhook trigger
    EVENT = "EVENT"             # System event trigger


class ConditionType(str, Enum):
    """Edge condition types for workflow routing"""
    SUCCESS = "SUCCESS"         # Execute if previous node succeeded
    FAILURE = "FAILURE"         # Execute if previous node failed
    ALWAYS = "ALWAYS"           # Always execute (default path)
    CONDITIONAL = "CONDITIONAL" # Execute based on custom condition


# ============================================================================
# SCRIPT ENUMS
# ============================================================================

class ScriptApprovalStatus(str, Enum):
    """Custom script approval status"""
    PENDING = "PENDING"         # Awaiting review
    APPROVED = "APPROVED"       # Approved for use
    REJECTED = "REJECTED"       # Rejected, cannot be used
    REVISION_NEEDED = "REVISION_NEEDED"  # Needs changes before approval


class ScriptTestStatus(str, Enum):
    """Custom script testing status"""
    UNTESTED = "UNTESTED"       # Not yet tested
    TESTING = "TESTING"         # Currently being tested
    PASSED = "PASSED"           # All tests passed
    FAILED = "FAILED"           # Tests failed
    PARTIAL = "PARTIAL"         # Some tests passed


# ============================================================================
# AUTHENTICATION ENUMS
# ============================================================================

class LoginStatus(str, Enum):
    """Login attempt status"""
    SUCCESS = "SUCCESS"                 # Login successful
    FAILED_INVALID_CREDENTIALS = "FAILED_INVALID_CREDENTIALS"  # Wrong password/email
    FAILED_ACCOUNT_LOCKED = "FAILED_ACCOUNT_LOCKED"            # Account locked
    FAILED_ACCOUNT_DISABLED = "FAILED_ACCOUNT_DISABLED"        # Account disabled
    FAILED_EMAIL_NOT_VERIFIED = "FAILED_EMAIL_NOT_VERIFIED"    # Email not verified
    FAILED_MFA_REQUIRED = "FAILED_MFA_REQUIRED"                # MFA required
    FAILED_MFA_INVALID = "FAILED_MFA_INVALID"                  # Invalid MFA code
    FAILED_RATE_LIMITED = "FAILED_RATE_LIMITED"                # Too many attempts
    FAILED_SUSPICIOUS = "FAILED_SUSPICIOUS"                    # Suspicious activity detected


class LoginMethod(str, Enum):
    """Login authentication method"""
    PASSWORD = "PASSWORD"           # Email/password login
    GOOGLE = "GOOGLE"              # Google OAuth
    GITHUB = "GITHUB"              # GitHub OAuth
    MICROSOFT = "MICROSOFT"        # Microsoft OAuth
    SSO = "SSO"                    # Single Sign-On
    API_KEY = "API_KEY"            # API key authentication
    TOKEN = "TOKEN"                # Token-based auth


class DeviceType(str, Enum):
    """Device type for login tracking"""
    DESKTOP = "DESKTOP"         # Desktop computer
    MOBILE = "MOBILE"           # Mobile phone
    TABLET = "TABLET"           # Tablet device
    BOT = "BOT"                 # Automated bot/crawler
    UNKNOWN = "UNKNOWN"         # Cannot determine device type


class PasswordChangeReason(str, Enum):
    """Password change reason"""
    VOLUNTARY = "VOLUNTARY"           # User voluntarily changed password
    RESET = "RESET"                   # Password changed via reset
    EXPIRED = "EXPIRED"               # Password expired and forced change
    FORCED = "FORCED"                 # Admin forced password change
    SECURITY_BREACH = "SECURITY_BREACH"  # Changed due to security breach


# ============================================================================
# RESOURCE ENUMS
# ============================================================================

class DatabaseType(str, Enum):
    """Database connection types"""
    POSTGRESQL = "POSTGRESQL"   # PostgreSQL
    MYSQL = "MYSQL"             # MySQL/MariaDB
    MONGODB = "MONGODB"         # MongoDB
    REDIS = "REDIS"             # Redis
    MSSQL = "MSSQL"             # Microsoft SQL Server
    ORACLE = "ORACLE"           # Oracle Database
    SQLITE = "SQLITE"           # SQLite
    CASSANDRA = "CASSANDRA"     # Apache Cassandra
    ELASTICSEARCH = "ELASTICSEARCH"  # Elasticsearch
    DYNAMODB = "DYNAMODB"       # AWS DynamoDB
    BIGQUERY = "BIGQUERY"       # Google BigQuery
    SNOWFLAKE = "SNOWFLAKE"     # Snowflake
    REDSHIFT = "REDSHIFT"       # AWS Redshift


class CredentialType(str, Enum):
    """Credential types"""
    API_KEY = "API_KEY"                 # Simple API key
    SLACK = "SLACK"                     # Slack credentials (bot_token, signing_secret, app_token)
    OAUTH2 = "OAUTH2"                   # OAuth 2.0 credentials
    BASIC_AUTH = "BASIC_AUTH"           # Username/password
    JWT = "JWT"                         # JSON Web Token
    AWS_CREDENTIALS = "AWS_CREDENTIALS" # AWS access key/secret
    GCP_SERVICE_ACCOUNT = "GCP_SERVICE_ACCOUNT"  # GCP service account
    SSH_KEY = "SSH_KEY"                 # SSH private key
    BEARER_TOKEN = "BEARER_TOKEN"       # Bearer token
    CUSTOM = "CUSTOM"                   # Custom credential format
    
class CredentialProvider(str, Enum):
    """Credential provider types"""
    GOOGLE = "GOOGLE"                # Custom credential format
    MICROSOFT = "MICROSOFT"          # Microsoft
    GITHUB = "GITHUB"                # GitHub


# ============================================================================
# PAYMENT & BILLING ENUMS
# ============================================================================

class TransactionType(str, Enum):
    """Payment transaction types"""
    PAYMENT = "PAYMENT"                 # Regular payment
    REFUND = "REFUND"                   # Refund transaction
    CHARGEBACK = "CHARGEBACK"           # Chargeback from bank
    ADJUSTMENT = "ADJUSTMENT"           # Manual adjustment
    CREDIT_APPLIED = "CREDIT_APPLIED"   # Credit/coupon applied


class TransactionStatus(str, Enum):
    """Payment transaction status"""
    PENDING = "PENDING"             # Transaction pending
    PROCESSING = "PROCESSING"       # Being processed
    SUCCESS = "SUCCESS"             # Transaction successful
    FAILED = "FAILED"               # Transaction failed
    CANCELLED = "CANCELLED"         # Transaction cancelled
    REFUNDED = "REFUNDED"           # Transaction refunded
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"  # Partial refund


class PaymentMethodType(str, Enum):
    """Payment method types"""
    CARD = "CARD"                   # Credit/debit card
    BANK_ACCOUNT = "BANK_ACCOUNT"   # Bank account (ACH)
    PAYPAL = "PAYPAL"               # PayPal
    SEPA_DEBIT = "SEPA_DEBIT"       # SEPA Direct Debit
    ALIPAY = "ALIPAY"               # Alipay
    WECHAT = "WECHAT"               # WeChat Pay
    CASH = "CASH"                   # Cash payment
    CHECK = "CHECK"                 # Check payment
    OTHER = "OTHER"                 # Other payment method


# ============================================================================
# NOTIFICATION ENUMS
# ============================================================================

class NotificationType(str, Enum):
    """Notification delivery channel types"""
    EMAIL = "EMAIL"           # Email notification
    SMS = "SMS"               # SMS notification
    PUSH = "PUSH"             # Push notification (mobile/web)
    IN_APP = "IN_APP"         # In-app notification
    WEBHOOK = "WEBHOOK"       # Webhook notification


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "PENDING"       # Queued for delivery
    SENDING = "SENDING"       # Currently being sent
    SENT = "SENT"             # Successfully sent
    DELIVERED = "DELIVERED"   # Delivered to recipient
    FAILED = "FAILED"         # Delivery failed
    BOUNCED = "BOUNCED"       # Email bounced
    READ = "READ"             # Read by recipient (in-app)


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "LOW"               # Low priority (can be batched)
    NORMAL = "NORMAL"         # Normal priority
    HIGH = "HIGH"             # High priority (send immediately)
    URGENT = "URGENT"         # Urgent (critical alerts)


class NotificationCategory(str, Enum):
    """Notification category for filtering and organization"""
    SYSTEM = "SYSTEM"             # System-generated notifications
    USER = "USER"                 # User-to-user notifications
    ADMIN = "ADMIN"               # Admin announcements
    SECURITY = "SECURITY"         # Security alerts
    WORKFLOW = "WORKFLOW"         # Workflow-related notifications
    EXECUTION = "EXECUTION"       # Execution status notifications
    SUBSCRIPTION = "SUBSCRIPTION" # Subscription & billing notifications
    MARKETING = "MARKETING"       # Marketing & promotional messages
    MAINTENANCE = "MAINTENANCE"   # System maintenance notifications


# ============================================================================
# AUDIT & ACCESS LOGS
# ============================================================================

class AuditAction(str, Enum):
    """Audit log actions - what user did"""
    # Workflow actions
    WORKFLOW_VIEWED = "WORKFLOW_VIEWED"
    WORKFLOW_CREATED = "WORKFLOW_CREATED"
    WORKFLOW_UPDATED = "WORKFLOW_UPDATED"
    WORKFLOW_DELETED = "WORKFLOW_DELETED"
    WORKFLOW_EXECUTED = "WORKFLOW_EXECUTED"
    WORKFLOW_CLONED = "WORKFLOW_CLONED"
    WORKFLOW_EXPORTED = "WORKFLOW_EXPORTED"
    
    # Credential actions (CRITICAL - sensitive data)
    CREDENTIAL_VIEWED = "CREDENTIAL_VIEWED"
    CREDENTIAL_VALUE_VIEWED = "CREDENTIAL_VALUE_VIEWED"  # CRITICAL!
    CREDENTIAL_CREATED = "CREDENTIAL_CREATED"
    CREDENTIAL_UPDATED = "CREDENTIAL_UPDATED"
    CREDENTIAL_DELETED = "CREDENTIAL_DELETED"
    CREDENTIAL_USED = "CREDENTIAL_USED"
    
    # Database actions
    DATABASE_VIEWED = "DATABASE_VIEWED"
    DATABASE_CONNECTION_STRING_VIEWED = "DATABASE_CONNECTION_STRING_VIEWED"  # CRITICAL!
    DATABASE_CREATED = "DATABASE_CREATED"
    DATABASE_UPDATED = "DATABASE_UPDATED"
    DATABASE_DELETED = "DATABASE_DELETED"
    DATABASE_CONNECTION_USED = "DATABASE_CONNECTION_USED"
    
    # Variable actions
    VARIABLE_VIEWED = "VARIABLE_VIEWED"
    VARIABLE_VALUE_VIEWED = "VARIABLE_VALUE_VIEWED"  # CRITICAL!
    VARIABLE_CREATED = "VARIABLE_CREATED"
    VARIABLE_UPDATED = "VARIABLE_UPDATED"
    VARIABLE_DELETED = "VARIABLE_DELETED"
    VARIABLE_USED = "VARIABLE_USED"
    
    # File actions
    FILE_VIEWED = "FILE_VIEWED"
    FILE_DOWNLOADED = "FILE_DOWNLOADED"
    FILE_UPLOADED = "FILE_UPLOADED"
    FILE_UPDATED = "FILE_UPDATED"
    FILE_DELETED = "FILE_DELETED"
    FILE_CONTENT_VIEWED = "FILE_CONTENT_VIEWED"
    
    # API Key actions
    API_KEY_VIEWED = "API_KEY_VIEWED"
    API_KEY_VALUE_VIEWED = "API_KEY_VALUE_VIEWED"  # CRITICAL!
    API_KEY_CREATED = "API_KEY_CREATED"
    API_KEY_UPDATED = "API_KEY_UPDATED"
    API_KEY_DELETED = "API_KEY_DELETED"
    API_KEY_USED = "API_KEY_USED"
    API_KEY_REGENERATED = "API_KEY_REGENERATED"  # CRITICAL!
    API_KEY_REVOKED = "API_KEY_REVOKED"
    
    # Permission actions
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    PERMISSION_UPDATED = "PERMISSION_UPDATED"
    
    # Workspace actions
    WORKSPACE_CREATED = "WORKSPACE_CREATED"
    WORKSPACE_UPDATED = "WORKSPACE_UPDATED"
    WORKSPACE_DELETED = "WORKSPACE_DELETED"
    WORKSPACE_MEMBER_ADDED = "WORKSPACE_MEMBER_ADDED"
    WORKSPACE_MEMBER_REMOVED = "WORKSPACE_MEMBER_REMOVED"
    WORKSPACE_MEMBER_ROLE_CHANGED = "WORKSPACE_MEMBER_ROLE_CHANGED"
    
    # Subscription & Billing actions
    SUBSCRIPTION_UPGRADED = "SUBSCRIPTION_UPGRADED"
    SUBSCRIPTION_DOWNGRADED = "SUBSCRIPTION_DOWNGRADED"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    INVOICE_GENERATED = "INVOICE_GENERATED"
    
    # Script actions
    SCRIPT_VIEWED = "SCRIPT_VIEWED"
    SCRIPT_CREATED = "SCRIPT_CREATED"
    SCRIPT_UPDATED = "SCRIPT_UPDATED"
    SCRIPT_DELETED = "SCRIPT_DELETED"
    SCRIPT_APPROVED = "SCRIPT_APPROVED"
    SCRIPT_REJECTED = "SCRIPT_REJECTED"
    
    # Execution actions
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EXECUTION_CANCELLED = "EXECUTION_CANCELLED"


class AuditStatus(str, Enum):
    """Audit log status - result of action"""
    SUCCESS = "SUCCESS"       # Action completed successfully
    FAILED = "FAILED"         # Action failed (error, exception)
    DENIED = "DENIED"         # Action denied (permission issue)
    PARTIAL = "PARTIAL"       # Action partially completed


class ResourceType(str, Enum):
    """Resource types for audit logging"""
    WORKFLOW = "WORKFLOW"
    NODE = "NODE"
    EDGE = "EDGE"
    TRIGGER = "TRIGGER"
    CREDENTIAL = "CREDENTIAL"
    DATABASE = "DATABASE"
    VARIABLE = "VARIABLE"
    FILE = "FILE"
    API_KEY = "API_KEY"
    WORKSPACE = "WORKSPACE"
    WORKSPACE_MEMBER = "WORKSPACE_MEMBER"
    WORKSPACE_INVITATION = "WORKSPACE_INVITATION"
    SUBSCRIPTION = "SUBSCRIPTION"
    INVOICE = "INVOICE"
    PAYMENT_METHOD = "PAYMENT_METHOD"
    SCRIPT = "SCRIPT"
    CUSTOM_SCRIPT = "CUSTOM_SCRIPT"
    EXECUTION = "EXECUTION"
    USER = "USER"
    PERMISSION = "PERMISSION"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Subscription & Billing
    'SubscriptionStatus',
    'InvoiceStatus',
    'InvitationStatus',
    
    # Workflow & Execution
    'WorkflowStatus',
    'ExecutionStatus',
    'TriggerType',
    'ConditionType',
    
    # Scripts
    'ScriptApprovalStatus',
    'ScriptTestStatus',
    
    # Authentication
    'LoginStatus',
    'LoginMethod',
    'DeviceType',
    'PasswordChangeReason',
    
    # Resources
    'DatabaseType',
    'CredentialType',
    
    # Payment & Billing
    'TransactionType',
    'TransactionStatus',
    'PaymentMethodType',
    
    # Notifications
    'NotificationType',
    'NotificationStatus',
    'NotificationPriority',
    'NotificationCategory',
    
    # Audit & Access Logs
    'AuditAction',
    'AuditStatus',
    'ResourceType',
]

