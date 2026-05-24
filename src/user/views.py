from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import UserLoginSerializer, UserLogoutSerializer
from .throttling import LoginThrottle


class UserTokenRefreshView(TokenRefreshView):
    authentication_classes = [JWTAuthentication]


class UserLoginView(APIView):
    """User Login API View"""

    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """User LogOut View"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserLogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "Logout successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
