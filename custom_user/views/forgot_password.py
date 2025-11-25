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
    """
    Parolni unutgan user uchun email'ga 6 raqamli kod yuborish.
    IP address bilan ishlaydi - har safar yangi IP'dan so'rov kelsa,
    eski kod bekor qilinadi va yangi kod yuboriladi.
    """
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
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)

        try:
            user = User.objects.get(email=email)

            # Agar user active bo'lmasa
            if not user.is_active:
                return Response(
                    {'error': 'Bu akkount aktivlashtirilmagan'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Oxirgi kod yuborilgan vaqtni tekshirish
            cache_key = f'reset_password_code_{user.id}'
            cached_data = cache.get(cache_key)

            if cached_data:
                # Agar IP bir xil bo'lsa va 1 daqiqa o'tmagan bo'lsa
                if cached_data.get('ip_address') == ip_address:
                    last_sent_key = f'last_reset_sent_{user.id}_{ip_address}'
                    if cache.get(last_sent_key):
                        return Response(
                            {'error': 'Iltimos, yangi kod so\'rash uchun 1 daqiqa kuting'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS
                        )
                else:
                    # Boshqa IP'dan kelsa, eski cache'ni o'chiramiz
                    cache.delete(cache_key)

            # Yangi kod generatsiya
            code = ''.join(random.choices(string.digits, k=6))

            # Cache'ga saqlash
            cache_data = {
                'email': email,
                'code': code,
                'ip_address': ip_address,
                'user_id': user.id
            }
            cache.set(cache_key, cache_data, timeout=600)  # 10 daqiqa
            cache.set(f'last_reset_sent_{user.id}_{ip_address}', True, timeout=60)

            # Email yuborish
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
                    {'error': 'Email yuborishda xatolik yuz berdi'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            response_data = {
                'success': True,
                'message': 'Parol tiklash kodi emailingizga yuborildi',
                'email': email
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'Bu email bilan foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )


class ForgotPasswordCompleteView(APIView):
    """
    Forgot password jarayonini yakunlash.
    UUID (reset_token) va yangi parol bilan parolni o'zgartirish.

    Jarayon:
    1. User forgot password so'raydi → Kod yuboriladi
    2. Universal verify'da kod tekshiriladi → UUID yaratiladi va qaytariladi
    3. Bu API UUID'ni tekshiradi → Yangi parolni o'rnatadi
    """
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
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        # Cache'dan token ma'lumotlarini olish
        reset_cache_key = f'password_reset_token_{reset_token}'
        token_data = cache.get(reset_cache_key)

        if not token_data:
            return Response(
                {'error': 'Noto\'g\'ri yoki muddati tugagan token. Iltimos, qaytadan urinib ko\'ring'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = token_data.get('user_id')

        try:
            user = User.objects.get(id=user_id)

            if not user.is_active:
                return Response(
                    {'error': 'Bu akkount aktivlashtirilmagan'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Yangi parolni o'rnatish
            user.set_password(new_password)
            user.save()

            # Cache'ni tozalash
            cache.delete(reset_cache_key)

            response_data = {
                'success': True,
                'message': 'Parol muvaffaqiyatli o\'zgartirildi. Endi login qilishingiz mumkin'
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
