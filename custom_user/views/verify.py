from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse

from custom_user.serializers import (
    DeviceSerializer,
    VerifyCodeUniversalSerializer,
    ErrorResponseSerializer,
    VerifyCodeUniversalResponseSerializer,
)
from custom_user.services import get_client_ip, get_location_by_ip, get_device_info
from custom_user.models import Device
from custom_user.utils import get_tokens_for_user

User = get_user_model()


class VerifyCodeUniversalView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyCodeUniversalSerializer,
        responses={
            200: OpenApiResponse(
                response=VerifyCodeUniversalResponseSerializer,
                description='Kod muvaffaqiyatli tasdiqlandi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Noto\'g\'ri kod yoki validatsiya xatosi'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Boshqa qurilmadan tasdiqlash mumkin emas'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Foydalanuvchi topilmadi'
            ),
        },
        tags=['Authentication'],
        summary='Universal kod tekshirish',
        description='Register yoki Forgot password uchun kodni tasdiqlash'
    )
    def post(self, request):
        serializer = VerifyCodeUniversalSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]

            return Response(
                {'success': False, 'error': error_msg, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        request_type = serializer.validated_data['request_type']
        ip_address = get_client_ip(request)
        location_city = get_location_by_ip(ip_address)
        device = get_device_info(request)
        device_model = device.get('device_model')

        try:
            user = User.objects.get(email=email)

            if request_type == 'register':
                cache_key = f'activation_code_{user.id}'
            elif request_type == 'forgot':
                cache_key = f'reset_password_code_{user.id}'
            else:
                return Response(
                    {'success': False, 'error': 'request_type can only be "register" or "forgot"', 'errorStatus': 'data_credential'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cached_data = cache.get(cache_key)

            if not cached_data:
                return Response(
                    {'success': False, 'error': 'Code has expired. Request a new code.', 'errorStatus': 'time_out'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if cached_data.get('ip_address') != ip_address:
                return Response(
                    { 'success': False,
                        'error': 'The code has been sent to another device. Please confirm on the device where the code was sent or request a new code.',
                      'errorStatus': 'another_device'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if cached_data.get('code') != code:
                return Response(
                    { 'success': False, 'error': 'Invalid code', 'errorStatus': 'data_credential'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ========== REGISTER TYPE ==========
            if request_type == 'register':
                device_hardware_from_request = serializer.validated_data.get('device_hardware')
                tokens = get_tokens_for_user(user, device_hardware=device_hardware_from_request)

                device = None
                if device_hardware_from_request:
                    device, created = Device.objects.update_or_create(
                        user=user,
                        device_hardware=device_hardware_from_request,
                        defaults={
                            'device_ip': ip_address,
                            'device_name': device_model,
                            'location_city': location_city if location_city else '',
                            'access_token': tokens['access'],
                            'refresh_token': tokens['refresh'],
                        }
                    )

                cache.delete(cache_key)
                cache.delete(f'last_code_sent_{user.id}_{ip_address}')

                response_data = {
                    'success': True,
                    'message': 'Akkount muvaffaqiyatli aktivlashtirildi',
                    'response': {
                        'access': tokens['access'],
                        'refresh': tokens['refresh'],
                    }
                }

                if device:
                    response_data['device'] = DeviceSerializer(device).data

                return Response(response_data, status=status.HTTP_200_OK)

            # ========== FORGOT TYPE ==========
            elif request_type == 'forgot':
                if not user.is_active:
                    return Response(
                        {'success': False, 'error': 'This account has not been activated.', 'errorStatus': 'unauthorized'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                import uuid as uuid_lib
                reset_token = uuid_lib.uuid4()

                reset_cache_key = f'password_reset_token_{reset_token}'
                cache.set(reset_cache_key, {
                    'user_id': user.id,
                    'email': email,
                    'ip_address': ip_address,
                }, timeout=900)

                cache.delete(cache_key)
                cache.delete(f'last_reset_sent_{user.id}_{ip_address}')

                response_data = {
                    'success': True,
                    'message': 'The code has been verified. Now set your new password.',
                    'reset_token': str(reset_token)
                }

                return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'success': False, 'error': 'No user found with this email.', 'errorStatus': 'exists'},
                status=status.HTTP_404_NOT_FOUND
            )

