import random
import string
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail

from drf_spectacular.utils import extend_schema, OpenApiResponse
from custom_user.serializers import (
    ForgotPasswordSerializer,
    ForgotPasswordResponseSerializer,
    ErrorResponseSerializer,
    ForgotPasswordCompleteSerializer,
    ForgotPasswordCompleteResponseSerializer
)
from custom_user.services import get_client_ip

User = get_user_model()


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=ForgotPasswordResponseSerializer,
                description='Parol tiklash kodi email\'ga yuborildi'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Foydalanuvchi topilmadi'
            ),
            429: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Juda ko\'p so\'rovlar'
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Email yuborishda xatolik'
            ),
        },
        tags=['Password Reset'],
        summary='Parolni unutdim',
        description='Email\'ga parol tiklash kodini yuborish'
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]

            return Response(
                {'success': False, 'error': error_msg, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)

        try:
            user = User.objects.get(email=email)

            if not user.is_active:
                return Response(
                    {'success': False, 'error': 'This account has not been activated.', 'errorStatus': 'not_activated'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cache_key = f'reset_password_code_{user.id}'
            cached_data = cache.get(cache_key)

            if cached_data:
                if cached_data.get('ip_address') == ip_address:
                    last_sent_key = f'last_reset_sent_{user.id}_{ip_address}'
                    if cache.get(last_sent_key):
                        return Response(
                            {'success': False, 'error': 'Please wait 1 minute to request a new code.', 'errorStatus': 'time_out'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS
                        )
                else:
                    cache.delete(cache_key)

            code = ''.join(random.choices(string.digits, k=6))

            cache_data = {
                'email': email,
                'code': code,
                'ip_address': ip_address,
                'user_id': user.id
            }
            cache.set(cache_key, cache_data, timeout=60)
            cache.set(f'last_reset_sent_{user.id}_{ip_address}', True, timeout=60)

            try:
                send_mail(
                    subject='Parolni tiklash kodi',
                    message=f'Assalomu alaykum!\n\nParolni tiklash kodingiz: {code}\n\nKod 10 daqiqa amal qiladi.\n\nAgar siz bu so\'rovni yuborgan bo\'lmasangiz, bu xabarni e\'tiborsiz qoldiring.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response(
                    {'success': False, 'error': 'An error occurred while sending the email.', 'errorStatus': 'send_mail'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            response_data = {
                'success': True,
                'message': 'A password recovery code has been sent to your email.',
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'success': False, 'error': 'No user found with this email.', 'errorStatus': 'exists'},
                status=status.HTTP_404_NOT_FOUND
            )


class ForgotPasswordCompleteView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordCompleteSerializer,
        responses={
            200: OpenApiResponse(
                response=ForgotPasswordCompleteResponseSerializer,
                description='Parol muvaffaqiyatli o\'zgartirildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Validatsiya xatosi'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Noto\'g\'ri yoki muddati tugagan token'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Foydalanuvchi topilmadi'
            ),
        },
        tags=['Password Reset'],
        summary='Forgot Password - yakunlash',
        description='Reset token (UUID) va yangi parol bilan parolni o\'zgartirish'
    )
    def post(self, request):
        serializer = ForgotPasswordCompleteSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]

            return Response(
                {'success': False, 'error': error_msg, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        reset_cache_key = f'password_reset_token_{reset_token}'
        token_data = cache.get(reset_cache_key)

        if not token_data:
            return Response(
                {'success': False, 'error': 'Invalid or expired token. Please try again.', 'errorStatus': 'data_credential'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = token_data.get('user_id')

        try:
            user = User.objects.get(id=user_id)

            if not user.is_active:
                return Response(
                    {'success': False, 'error': 'This account has not been activated.', 'errorStatus': 'unauthorized'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.save()

            cache.delete(reset_cache_key)

            response_data = {
                'success': True,
                'message': 'Password changed successfully. You can now log in.'
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'success': False, 'error': 'User not found.', 'errorStatus': 'exists'},
                status=status.HTTP_404_NOT_FOUND
            )
