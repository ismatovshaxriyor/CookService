from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
import random
import string

from custom_user.serializers import (
    SendActivationCodeSerializer,
    SendActivationCodeResponseSerializer,
    ErrorResponseSerializer,
)
from custom_user.services import get_client_ip

User = get_user_model()


class SendActivationCodeView(APIView):
    """
    Foydalanuvchiga email orqali 6 raqamli aktivatsiya kodini yuboradi.
    Kod 5 daqiqa davomida amal qiladi.
    Har safar yangi IP'dan so'rov kelganda eski cache bekor qilinadi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=SendActivationCodeSerializer,
        responses={
            200: OpenApiResponse(
                response=SendActivationCodeResponseSerializer,
                description='Aktivatsiya kodi muvaffaqiyatli yuborildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Email talab qilinadi yoki akkount allaqachon aktivlashtirilgan'
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
        tags=['Authentication'],
        summary='Aktivatsiya kodini qayta yuborish',
        description='Foydalanuvchining emailiga 6 raqamli aktivatsiya kodini qayta yuboradi'
    )
    def post(self, request):
        serializer = SendActivationCodeSerializer(data=request.data)

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

            if user.is_active:
                return Response(
                    {'status': False, 'error': 'This account is already activated.', 'errorStatus': 'already_have'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cache_key = f'activation_code_{user.id}'
            cached_data = cache.get(cache_key)

            if cached_data:
                if cached_data.get('ip_address') == ip_address:
                    last_sent_key = f'last_code_sent_{user.id}_{ip_address}'
                    if cache.get(last_sent_key):
                        return Response(
                            {'status': False, 'error': 'Please wait 1 minute to request a new code.',
                             'errorStatus': 'time_out'},
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
            cache.set(cache_key, cache_data, timeout=20)
            cache.set(f'last_code_sent_{user.id}_{ip_address}', True, timeout=60)

            try:
                send_mail(
                    subject='Aktivatsiya kodi',
                    message=f'Assalomu alaykum!\n\nSizning aktivatsiya kodingiz: {code}\n\nKod 5 daqiqa amal qiladi.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response(
                    {'success': False, 'error': 'An error occurred while sending the email.', "errorStatus": "data_credential"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            response_data = {
                'success': True,
                'message': 'The activation code has been sent to your email.',
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'success': False, 'error': 'No user found with this email.', 'errorStatus': 'data_credential'},
                status=status.HTTP_404_NOT_FOUND
            )

