from rest_framework.response import Response
from rest_framework import status
from ..services.auth_services import AuthService
from bson import ObjectId
import logging
from functools import wraps
import traceback

logger = logging.getLogger(__name__)

def get_authenticated_user_from_jwt(request):
    """Helper function to get authenticated user from JWT token"""
    try:
        if not hasattr(request, 'headers'):
            logger.error(f"Request object missing headers attribute: {type(request)}")
            return None
            
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            logger.debug("No Bearer token found in Authorization header")
            return None
        
        token = authorization.split(" ", 1)[1]
        logger.debug(f"Extracted token: {token[:20]}...")
         
        auth_service = AuthService()
        user_data = auth_service.get_current_user(token)
        
        if not user_data or not user_data.get('user_id'):
            logger.debug("No valid user data from token")
            return None
        
        user_id = user_data.get('user_id')
        user_doc = auth_service.user_collection.find_one({
            "_id": ObjectId(user_id),
            "isDeleted": {"$ne": True}
        })
        
        if not user_doc or user_doc.get("status", "active") != "active":
            logger.debug(f"User document not found, deleted, or inactive: {user_id}")
            return None
        
        username = user_doc.get('username', '').strip()
        display_username = username or user_doc.get('email', 'unknown')

        return {
            "user_id": user_id,
            "username": display_username,
            "email": user_doc.get('email'),
            "full_name": user_doc.get('full_name', ''),
            "role": user_doc.get('role', 'employee')
        }

    except Exception as e:
        logger.error(f"JWT authentication error: {e}")
        traceback.print_exc()
        return None

# ================================================================
# SIMPLIFIED AUTHENTICATION DECORATORS
# ================================================================

def require_authentication(view_func):
    """Decorator for any authenticated user (admin or employee)"""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if len(args) >= 2:
            request = args[1]
        elif len(args) == 1:
            request = args[0]
        else:
            request = kwargs.get('request')
            
        if not request or not hasattr(request, 'headers'):
            return Response(
                {"error": "Invalid request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_user = get_authenticated_user_from_jwt(request)
        if not current_user:
            return Response(
                {"error": "Authentication required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        request.current_user = current_user
        return view_func(*args, **kwargs)
    return wrapper

def require_admin(view_func):
    """Decorator for admin-only functions"""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if len(args) >= 2:
            request = args[1]
        elif len(args) == 1:
            request = args[0]
        else:
            request = kwargs.get('request')
            
        if not request or not hasattr(request, 'headers'):
            return Response(
                {"error": "Invalid request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_user = get_authenticated_user_from_jwt(request)
        if not current_user:
            return Response(
                {"error": "Authentication required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if current_user.get('role', '').lower() != 'admin':
            return Response(
                {"error": "Admin access required"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        request.current_user = current_user
        return view_func(*args, **kwargs)
    return wrapper