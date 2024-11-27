from django.db import transaction

from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response

from src.user.public.serializers import PublicUserSignUpSerializer


class PublicUserSignUpAPIView(generics.CreateAPIView):
    """Signup User using different third party applications"""

    permission_classes = [AllowAny]
    serializer_class = PublicUserSignUpSerializer
    # throttle_classes = [None]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(
                serializer.validated_data["auth_token"], status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

