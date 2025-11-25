from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
from custom_user.serializers import (
    ResetPasswordSerializer,
    ResetPasswordResponseSerializer,
    ErrorResponseSerializer
)

User = get_user_model()


class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=ResetPasswordResponseSerializer,
                description='Parol muvaffaqiyatli o\'zgartirildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Eski parol noto\'g\'ri'
            ),
        },
        tags=['Password Reset'],
        summary='Parolni o\'zgartirish',
        description='Authenticated user uchun parolni yangilash (eski parol kerak)'
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_password = serializer.validated_data['new_password']
        user = request.user

        user.set_password(new_password)
        user.save()

        response_data = {
            'success': True,
            'message': 'Parol muvaffaqiyatli o\'zgartirildi'
        }

        return Response(response_data, status=status.HTTP_200_OK)