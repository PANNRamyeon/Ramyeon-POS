from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from ..services.auth_services import AuthService
from ..services.session_services import SessionLogService 
import logging
from ..decorators.authenticationDecorator import require_authentication, require_admin

# ================ AUTHENTICATION VIEWS ================

class LoginView(APIView):
    def post(self, request):
        """User login"""
        try:
            auth_service = AuthService()
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return Response(
                    {"error": "Email and password are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = auth_service.login(email, password)
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(APIView):
    @require_authentication
    def post(self, request):
    
        """User logout with session logging"""
        try:
            auth_service = AuthService()
            session_service = SessionLogService()  # ✅ ADD THIS
            
            current_user = request.current_user
            user_id = current_user.get('user_id')
            
            if not user_id: 
                return Response(
                    {"error": "Unable to identify user for logout"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # # Log session logout first
            try:
                session_service.log_logout(user_id)
            except Exception as session_error:
                # Log the error but don't fail the logout
                print(f"Session logout failed: {session_error}")

            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            result = auth_service.logout(token)
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RefreshTokenView(APIView):
    def post(self, request):
        """Refresh access token"""
        try:
            auth_service = AuthService()
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = auth_service.refresh_access_token(refresh_token)
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

class CurrentUserView(APIView):
    def get(self, request):
        """Get current authenticated user"""
        try:
            auth_service = AuthService()
            
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return Response(
                    {"error": "Missing or invalid authorization header"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            token = authorization.split(" ")[1]
            user = auth_service.get_current_user(token)
            
            if user:
                return Response(user, status=status.HTTP_200_OK)
            
            return Response(
                {"error": "Invalid token"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyTokenView(APIView):
    def post(self, request):
        """Verify if token is valid"""
        try:
            auth_service = AuthService()
            
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
            else:
                token = request.data.get('token')
            
            if not token:
                return Response(
                    {"error": "Token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            payload = auth_service.verify_token(token)
            
            if payload:
                return Response({
                    "valid": True,
                    "user_id": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role")
                }, status=status.HTTP_200_OK)
            
            return Response(
                {"valid": False, "error": "Invalid token"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ChangePasswordView(APIView):
    def patch(self, request):
        """Change user password - partial update of user resource"""
        try:
            auth_service = AuthService()
            
            # Get token from header
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return Response(
                    {"error": "Missing or invalid authorization header"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            token = authorization.split(" ")[1]
            
            # Verify token and get user
            payload = auth_service.verify_token(token)
            if not payload or payload.get("type") != "access":
                return Response(
                    {"error": "Invalid token"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_id = payload["sub"]
            user = auth_service.user_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get password data from request
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
            
            if not current_password or not new_password:
                return Response(
                    {"error": "Current password and new password are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify current password
            if not auth_service.verify_password(current_password, user["password"]):
                return Response(
                    {"error": "Current password is incorrect"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Hash new password and update user
            hashed_new_password = auth_service.hash_password(new_password)
            
            auth_service.user_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password": hashed_new_password,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            return Response(
                {"message": "Password updated successfully"}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )