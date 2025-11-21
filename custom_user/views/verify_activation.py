from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.tokens import RefreshToken

from custom_user.serializers import (
    VerifyActivationCodeSerializer,
    VerifyActivationCodeResponseSerializer,
    ErrorResponseSerializer,
)
from custom_user.services import get_client_ip, get_device_info, get_location_by_ip
from custom_user.models import Device

User = get_user_model()


class VerifyActivationCodeView(APIView):
    """
    Yuborilgan aktivatsiya kodini tekshiradi, akkountni aktivlashtiradi
    va JWT tokenlarni qaytaradi (avtomatik login).
    IP address ham tekshiriladi - faqat kod yuborilgan qurilmadan tasdiqlash mumkin.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyActivationCodeSerializer,
        responses={
            200: OpenApiResponse(
                response=VerifyActivationCodeResponseSerializer,
                description='Akkount aktivlashtirildi va JWT tokenlar berildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Noto\'g\'ri kod yoki kod muddati tugagan'
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
        summary='Aktivatsiya kodini tekshirish va login',
        description='6 raqamli kodni tekshiradi, akkountni aktivlashtiradi va JWT tokenlar qaytaradi'
    )
    def post(self, request):
        serializer = VerifyActivationCodeSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]

            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        ip_address = get_client_ip(request)
        device = get_device_info(request)
        device_model = device.get('device_model')
        location = get_location_by_ip(ip_address)
        location_city = location.city

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response(
                    {'error': 'Bu akkount allaqachon aktivlashtirilgan'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cache_key = f'activation_code_{user.id}'
            cached_data = cache.get(cache_key)

            if not cached_data:
                return Response(
                    {'error': 'Aktivatsiya kodi muddati tugagan. Yangi kod so\'rang'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # IP address tekshiruvi
            if cached_data.get('ip_address') != ip_address:
                return Response(
                    {
                        'error': 'Kod boshqa qurilmaga yuborilgan. Kod yuborilgan qurilmadan tasdiqlang yoki yangi kod so\'rang'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if cached_data.get('code') == code:
                user.is_active = True
                user.save()

                device = Device.objects.create(
                    user=user,
                    device_ip=ip_address,
                    device_hardware=serializer.validated_data.get('device_hardware', ''),
                    device_name=device_model,
                    location_city=location_city,
                )

                cache.delete(cache_key)
                cache.delete(f'last_code_sent_{user.id}_{ip_address}')

                refresh = RefreshToken.for_user(user)

                response_data = {
                    'success': True,
                    'message': 'Akkount muvaffaqiyatli aktivlashtirildi',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Noto\'g\'ri aktivatsiya kodi'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except User.DoesNotExist:
            return Response(
                {'error': 'Bu email bilan foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

