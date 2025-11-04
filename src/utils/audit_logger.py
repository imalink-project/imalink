"""
Audit logging utility for tracking sensitive operations
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

# Configure audit logger
audit_logger = logging.getLogger("imalink.audit")
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs
file_handler = logging.FileHandler("audit.log")
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# Add handler to logger
audit_logger.addHandler(file_handler)


class AuditAction(str, Enum):
    """Enumeration of audit actions"""
    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    
    # Photo actions
    PHOTO_CREATE = "photo_create"
    PHOTO_UPDATE = "photo_update"
    PHOTO_DELETE = "photo_delete"
    PHOTO_VIEW = "photo_view"
    
    # Author actions
    AUTHOR_CREATE = "author_create"
    AUTHOR_UPDATE = "author_update"
    AUTHOR_DELETE = "author_delete"
    
    # Import session actions
    IMPORT_SESSION_CREATE = "import_session_create"
    IMPORT_SESSION_DELETE = "import_session_delete"
    
    # Tag actions
    TAG_CREATE = "tag_create"
    TAG_UPDATE = "tag_update"
    TAG_DELETE = "tag_delete"


def log_audit_event(
    action: AuditAction,
    user_id: int,
    username: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> None:
    """
    Log an audit event
    
    Args:
        action: Type of action performed
        user_id: ID of user performing action
        username: Username of user performing action
        resource_type: Type of resource (photo, author, etc.)
        resource_id: ID or hash of the resource
        details: Additional details about the action
        ip_address: IP address of the request
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action.value,
        "user_id": user_id,
        "username": username,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "ip_address": ip_address,
        "details": details or {}
    }
    
    audit_logger.info(
        f"ACTION={action.value} USER={username}({user_id}) "
        f"RESOURCE={resource_type}:{resource_id} "
        f"IP={ip_address} DETAILS={details}"
    )


def log_security_event(
    event_type: str,
    message: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a security-related event (failed logins, permission denials, etc.)
    
    Args:
        event_type: Type of security event
        message: Description of the event
        user_id: ID of user (if applicable)
        username: Username (if applicable)
        ip_address: IP address of the request
        details: Additional details
    """
    audit_logger.warning(
        f"SECURITY EVENT={event_type} MESSAGE={message} "
        f"USER={username}({user_id}) IP={ip_address} DETAILS={details}"
    )
