from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ...services.Backoffice.user_service import UserService
from ...decorators.authenticationDecorator import require_admin, require_authentication, require_permission, get_authenticated_user_from_jwt
from ...serializers import UserCreateSerializer
import logging
from datetime import datetime


logger = logging.getLogger(__name__)

# ================================================================
# VIEW CLASSES
# ================================================================

class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "message": "User Management API is running!",
            "status": "active",
            "version": "1.0.0"
        }, status=status.HTTP_200_OK)

class UserListView(APIView):
    def __init__(self):
        self.user_service = UserService()
    
    
    def get(self, request):
        """Get users with pagination and filters"""
        try:
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 50))
            status_filter = request.query_params.get('status')
            include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'
            
            # Only admins can view deleted users
            if include_deleted and request.current_user.get('role', '').lower() != 'admin':
                return Response(
                    {"error": "Admin permissions required to view deleted users"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            result = self.user_service.get_users(
                page=page, 
                limit=limit, 
                status=status_filter, 
                include_deleted=include_deleted
            )
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

   
    def post(self, request):
        """Create new user - Requires admin authentication"""
        try:
            serializer = UserCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Validation failed", "details": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            current_user = getattr(request, 'current_user', None)
            new_user = self.user_service.create_user(serializer.validated_data, current_user )
            return Response(new_user, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class UserDetailView(APIView):
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    @require_authentication
    def get(self, request, user_id):
        """Get user by ID (with optional deleted users for admin)"""
        try:
            include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'
            
            # Only admins can view deleted users
            if include_deleted:
                current_user = request.current_user 
                if not current_user or current_user.get('role', '').lower() != 'admin':
                    return Response(
                        {"error": "Admin permissions required to view deleted users"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            user = self.user_service.get_user_by_id(user_id, include_deleted=include_deleted)
            if not user:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(user, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @require_authentication
    def put(self, request, user_id):
        """Update user - Admin only OR self-service password change"""
        try:
            from datetime import datetime
            
            current_user = request.current_user
            # Try multiple possible ID fields
            current_user_id = current_user.get('_id') or current_user.get('user_id') or current_user.get('id')
            
            request_data = request.data.copy()
            
            # Check if this is a password change request
            is_password_change = 'current_password' in request_data and 'new_password' in request_data
            
            # Determine if self-service
            is_self_service = current_user_id == user_id
            
            if is_self_service and is_password_change:
                # Get user
                user = self.user_service.get_user_by_id(user_id)
                if not user:
                    return Response(
                        {"error": "User not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Verify current password
                current_password = request_data.get('current_password')
                password_valid = self.user_service.verify_password(current_password, user['password'])
                
                if not password_valid:
                    return Response(
                        {"error": "Current password is incorrect"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Hash new password
                new_password = request_data.get('new_password')
                hashed_password = self.user_service.hash_password(new_password)
                
                # Prepare update data
                update_data = {
                    'password': hashed_password,
                    'last_updated': datetime.utcnow()
                }
                
                # Perform update
                result = self.user_service.collection.update_one(
                    {'_id': user_id, 'isDeleted': {'$ne': True}}, 
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    updated_user = self.user_service.get_user_by_id(user_id)
                    
                    # Send notification
                    user_name = updated_user.get('full_name', updated_user.get('username', 'User'))
                    self.user_service._send_user_notification('password_changed', user_name, user_id)
                    
                    return Response({
                        'success': True,
                        'message': 'Password updated successfully',
                        'data': updated_user
                    }, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"error": "Password was not updated"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            elif current_user.get('role', '').lower() == 'admin':
                # Admin updating user (not password change)
                
                # Remove password-related fields for regular updates
                update_data = {k: v for k, v in request_data.items() 
                            if k not in ['current_password', 'new_password', 'password']}
                update_data['last_updated'] = datetime.utcnow()
                
                result = self.user_service.collection.update_one(
                    {'_id': user_id, 'isDeleted': {'$ne': True}}, 
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    updated_user = self.user_service.get_user_by_id(user_id)
                    
                    # Send notification
                    user_name = updated_user.get('full_name', updated_user.get('username', 'User'))
                    self.user_service._send_user_notification('updated', user_name, user_id)
                    
                    return Response({
                        'success': True,
                        'message': 'User updated successfully',
                        'data': updated_user
                    }, status=status.HTTP_200_OK)
                
                return Response(
                    {"error": "No changes made"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            else:
                return Response(
                    {"error": "Insufficient permissions to update user"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @require_authentication
    def delete(self, request, user_id):
        """Soft delete user - Requires admin authentication"""
        try:
            deleted = self.user_service.soft_delete_user(user_id, request.current_user)
            
            if not deleted:
                return Response(
                    {"error": "User not found or already deleted"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {"message": "User deleted successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserRestoreView(APIView):
    """View for restoring soft-deleted users"""
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    @require_authentication
    def post(self, request, user_id):
        """Restore a soft-deleted user - Requires admin authentication"""
        try:
            restored = self.user_service.restore_user(user_id, request.current_user)
            
            if not restored:
                return Response(
                    {"error": "User not found or not deleted"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {"message": "User restored successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error restoring user {user_id}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserHardDeleteView(APIView):
    """View for permanently deleting users (DANGEROUS)"""
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    @require_authentication
    def delete(self, request, user_id):
        """PERMANENTLY delete user"""
        try:
            confirm = request.query_params.get('confirm', '').lower()
            if confirm != 'yes':
                return Response({
                    "error": "Permanent deletion requires confirmation", 
                    "message": "Add ?confirm=yes to permanently delete this user"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use the confirmation token from service
            deleted = self.user_service.hard_delete_user(
                user_id, 
                request.current_user, 
                confirmation_token="PERMANENT_DELETE_CONFIRMED"
            )
            
            if not deleted:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                "message": "User permanently deleted"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DeletedUsersView(APIView):
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    @require_authentication
    def get(self, request):
        """Get soft-deleted users - Admin only"""
        try:
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 50))
            
            # Use get_users with include_deleted=True and deleted_only filter
            result = self.user_service.get_users(
                page=page, 
                limit=limit, 
                include_deleted=True
            )
            
            # Filter only deleted users
            deleted_users = [user for user in result['users'] if user.get('isDeleted') == True]
            
            return Response({
                'users': deleted_users,
                'total': len(deleted_users),
                'page': page,
                'limit': limit
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting deleted users: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserByEmailView(APIView):
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    @require_authentication    
    def get(self, request, email):
        """Get user by email (excludes deleted by default)"""
        try:
            include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'
            
            # Only admins can view deleted users
            if include_deleted:
                current_user = request.current_user
                if not current_user or current_user.get('role', '').lower() != 'admin':
                    return Response(
                        {"error": "Admin permissions required to view deleted users"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            user = self.user_service.get_user_by_email(email, include_deleted=include_deleted)
            if not user:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(user, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserByUsernameView(APIView):
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    @require_authentication    
    def get(self, request, username):
        """Get user by username (excludes deleted by default)"""
        try:
            include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'
            
            # Only admins can view deleted users
            if include_deleted:
                current_user = request.current_user
                if not current_user or current_user.get('role', '').lower() != 'admin':
                    return Response(
                        {"error": "Admin permissions required to view deleted users"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            user = self.user_service.get_user_by_username(username, include_deleted=include_deleted)
            if not user:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(user, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
