"""
Custom exceptions for ImaLink API
Provides structured error handling across the application
"""
from typing import Any, Optional, List, Dict


class APIException(Exception):
    """Base exception class for all API errors"""
    
    def __init__(self, message: str, code: str, status_code: int = 400, details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(APIException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource: str, id: Any):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND", 
            status_code=404
        )


class DuplicateImageError(APIException):
    """Raised when trying to create a duplicate image"""
    
    def __init__(self, message: str = "Image already exists"):
        super().__init__(
            message=message,
            code="DUPLICATE_IMAGE",
            status_code=409
        )


class DuplicatePhotoError(APIException):
    """Raised when trying to create a duplicate photo"""
    
    def __init__(self, message: str = "Photo already exists"):
        super().__init__(
            message=message,
            code="DUPLICATE_PHOTO",
            status_code=409
        )


class ValidationError(APIException):
    """Raised when request data fails validation"""
    
    def __init__(self, message: str, field_errors: Optional[List[Dict]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"field_errors": field_errors or []}
        )


class AuthorizationError(APIException):
    """Raised when user lacks permission for requested action"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403
        )


class AuthenticationError(APIException):
    """Raised when authentication is required or invalid"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR", 
            status_code=401
        )


class BusinessLogicError(APIException):
    """Raised when business rules are violated"""
    
    def __init__(self, message: str, code: str = "BUSINESS_LOGIC_ERROR"):
        super().__init__(
            message=message,
            code=code,
            status_code=400
        )


class ExternalServiceError(APIException):
    """Raised when external service calls fail"""
    
    def __init__(self, service: str, message: str = "External service unavailable"):
        super().__init__(
            message=f"{service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=503
        )