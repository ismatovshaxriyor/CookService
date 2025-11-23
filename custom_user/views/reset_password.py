from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
from custom_user.serializers import (
    ResetPasswordSerializer,
    ResetPasswordResponseSerializer,
    ErrorResponseSerializer
)
from custom_user.services import get_client_ip

User = get_user_model()

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=ResetPasswordResponseSerializer,
                description='Parol muvaffaqiyatli o\'zgartirildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Noto\'g\'ri kod yoki kod muddati tugagan'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Boshqa qurilmadan parol o\'zgartirish mumkin emas'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Foydalanuvchi topilmadi'
            ),
        },
        tags=['Password Reset'],
        summary='Parolni o\'zgartirish',
        description='Kod bilan parolni yangilash'
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': serializer.errors, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']
        ip_address = get_client_ip(request)

        try:
            user = User.objects.get(email=email)

            if not user.is_active:
                return Response(
                    {'success': False, 'error': 'This account has not been activated.', 'errorStatus': 'not_activated'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Cache'dan ma'lumotlarni olish
            cache_key = f'reset_password_code_{user.id}'
            cached_data = cache.get(cache_key)

            if not cached_data:
                return Response(
                    {'status': False, 'error': 'Code has expired. Request a new code.', 'errorStatus': 'time_out'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if cached_data.get('ip_address') != ip_address:
                return Response(
                    { "status": False,
                        'error': 'The code was sent to another device. Change the password on the device where the code was sent or request a new code.',
                      'errorStatus': 'another_device'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if cached_data.get('code') == code:
                user.set_password(new_password)
                user.save()

                cache.delete(cache_key)
                cache.delete(f'last_reset_sent_{user.id}_{ip_address}')

                response_data = {
                    'success': True,
                    'message': 'Password changed successfully.',
                }

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'status': False, 'error': 'Invalid code', "errorStatus": 'data_credential'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except User.DoesNotExist:
            return Response(
                {'status': False, 'error': 'No user found with this email.', "errorStatus": 'not_registered'},
                status=status.HTTP_404_NOT_FOUND
            )