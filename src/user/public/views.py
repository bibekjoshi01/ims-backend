from django.db import transaction

from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema

from .schemas import PublicUserLoginResponseSerializer
from src.user.public.serializers import PublicUserSignInSerializer


class PublicUserSignInAPIView(generics.CreateAPIView):
    """Signin User using different third party applications"""

    permission_classes = [AllowAny]
    serializer_class = PublicUserSignInSerializer
    throttle_classes = [AnonRateThrottle]

    @transaction.atomic
    @extend_schema(
        request=PublicUserSignInSerializer,
        responses={200: PublicUserLoginResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
