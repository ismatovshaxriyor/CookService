from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.tokens import RefreshToken

from custom_user.serializers import (
    VerifyCodeUniversalSerializer,
    ErrorResponseSerializer,
    DeviceSerializer,
     VerifyCodeUniversalResponseSerializer,
)
from custom_user.services import get_client_ip
from custom_user.models import Device

User = get_user_model()


class VerifyCodeUniversalView(APIView):
    """
    Universal kod tekshirish API.

    request_type='register':
        - User aktivatsiya qilinadi
        - JWT tokenlar beriladi
        - Device yaratiladi (agar ma'lumotlar bo'lsa)

    request_type='forgot':
        - Faqat kod tekshiriladi
        - Token BERILMAYDI
        - Keyingi qadamda user login qilishi kerak
    """
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
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        request_type = serializer.validated_data['request_type']
        ip_address = get_client_ip(request)

        try:
            user = User.objects.get(email=email)

            # Cache key request_type ga qarab tanlanadi
            if request_type == 'register':
                cache_key = f'activation_code_{user.id}'
            elif request_type == 'forgot':
                cache_key = f'reset_password_code_{user.id}'
            else:
                return Response(
                    {'error': 'request_type faqat "register" yoki "forgot" bo\'lishi mumkin'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Cache'dan ma'lumotlarni olish
            cached_data = cache.get(cache_key)

            if not cached_data:
                return Response(
                    {'error': 'Kod muddati tugagan. Yangi kod so\'rang'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # IP address tekshiruvi
            if cached_data.get('ip_address') != ip_address:
                return Response(
                    {
                        'error': 'Kod boshqa qurilmaga yuborilgan. Kod yuborilgan qurilmadan tasdiqlang yoki yangi kod so\'rang'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Kodni tekshirish
            if cached_data.get('code') != code:
                return Response(
                    {'error': 'Noto\'g\'ri kod'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ========== REGISTER TYPE ==========
            if request_type == 'register':
                # User aktivatsiya qilish
                if user.is_active:
                    return Response(
                        {'error': 'Bu akkount allaqachon aktivlashtirilgan'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user.is_active = True
                user.save()

                # Device yaratish (agar ma'lumotlar bo'lsa)
                device = None
                if serializer.validated_data.get('device_hardware') or serializer.validated_data.get('device_name'):
                    device = Device.objects.create(
                        user=user,
                        device_ip=ip_address,
                        device_hardware=serializer.validated_data.get('device_hardware', ''),
                        device_name=serializer.validated_data.get('device_name', ''),
                        location_city=serializer.validated_data.get('location_city', ''),
                    )

                # JWT tokenlarni generatsiya qilish
                refresh = RefreshToken.for_user(user)

                # Cache'ni tozalash
                cache.delete(cache_key)
                cache.delete(f'last_code_sent_{user.id}_{ip_address}')

                response_data = {
                    'success': True,
                    'message': 'Akkount muvaffaqiyatli aktivlashtirildi',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }

                # Device ma'lumotini qo'shish
                if device:
                    response_data['device'] = DeviceSerializer(device).data

                return Response(response_data, status=status.HTTP_200_OK)

            # ========== FORGOT TYPE ==========
            elif request_type == 'forgot':
                # Faqat kodni tasdiqlash, token BERMAYDI
                if not user.is_active:
                    return Response(
                        {'error': 'Bu akkount aktivlashtirilmagan'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Cache'ni tozalash
                cache.delete(cache_key)
                cache.delete(f'last_reset_sent_{user.id}_{ip_address}')

                response_data = {
                    'success': True,
                    'message': 'Kod tasdiqlandi. Endi login qiling',
                    'request_type': 'forgot',
                    'email': email
                }

                return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'Bu email bilan foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

