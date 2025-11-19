# users/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.tokens import RefreshToken
import random
import string

from .serializers import (
    UserRegistrationSerializer,
    UserRegistrationResponseSerializer,
    SendActivationCodeSerializer,
    SendActivationCodeResponseSerializer,
    VerifyActivationCodeSerializer,
    VerifyActivationCodeResponseSerializer,
    ErrorResponseSerializer,
    UserLoginSerializer,
    UserLoginResponseSerializer
)

User = get_user_model()


class UserRegistrationView(APIView):
    """
    Yangi user ro'yxatdan o'tish. User yaratiladi lekin is_active=False bo'ladi.
    Keyin email'ga aktivatsiya kodi yuboriladi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                response=UserRegistrationResponseSerializer,
                description='User muvaffaqiyatli yaratildi, email ga kod yuborildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Validatsiya xatosi'
            ),
        },
        tags=['Authentication'],
        summary="Ro'yxatdan o'tish",
        description='Yangi user yaratish va email ga aktivatsiya kodi yuborish'
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()

        # Aktivatsiya kodini generatsiya qilish va yuborish
        code = ''.join(random.choices(string.digits, k=6))
        cache.set(f'activation_code_{user.id}', code, timeout=300)  # 5 daqiqa

        # Email yuborish
        try:
            send_mail(
                subject='Aktivatsiya kodi',
                message=f'Assalomu alaykum!\n\nSizning aktivatsiya kodingiz: {code}\n\nKod 5 daqiqa amal qiladi.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Agar email yuborilmasa ham user yaratilgan bo'ladi
            pass

        response_data = {
            'success': True,
            'message': 'Ro\'yxatdan o\'tish muvaffaqiyatli. Email ga aktivatsiya kodi yuborildi',
            'email': user.email
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class SendActivationCodeView(APIView):
    """
    Foydalanuvchiga email orqali 6 raqamli aktivatsiya kodini yuboradi.
    Kod 5 daqiqa davomida amal qiladi.
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
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response(
                    {'error': 'Bu akkount allaqachon aktivlashtirilgan'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Oxirgi kod yuborilgan vaqtni tekshirish
            last_sent = cache.get(f'last_code_sent_{user.id}')
            if last_sent:
                return Response(
                    {'error': 'Iltimos, yangi kod so\'rash uchun 1 daqiqa kuting'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # 6 xonali kod generatsiya
            code = ''.join(random.choices(string.digits, k=6))

            # Kodni saqlash
            cache.set(f'activation_code_{user.id}', code, timeout=300)
            cache.set(f'last_code_sent_{user.id}', True, timeout=60)

            # Email yuborish
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
                    {'error': 'Email yuborishda xatolik yuz berdi'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            response_data = {
                'success': True,
                'message': 'Aktivatsiya kodi emailingizga yuborildi',
                'email': email
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'Bu email bilan foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )


class VerifyActivationCodeView(APIView):
    """
    Yuborilgan aktivatsiya kodini tekshiradi, akkountni aktivlashtiradi
    va JWT tokenlarni qaytaradi (avtomatik login).
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
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response(
                    {'error': 'Bu akkount allaqachon aktivlashtirilgan'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            saved_code = cache.get(f'activation_code_{user.id}')

            if not saved_code:
                return Response(
                    {'error': 'Aktivatsiya kodi muddati tugagan. Yangi kod so\'rang'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if saved_code == code:
                # Akkountni aktivlashtirish
                user.is_active = True
                user.save()

                # Cache'dan kodni o'chirish
                cache.delete(f'activation_code_{user.id}')
                cache.delete(f'last_code_sent_{user.id}')

                # JWT tokenlarni generatsiya qilish
                refresh = RefreshToken.for_user(user)

                response_data = {
                    'success': True,
                    'message': 'Akkount muvaffaqiyatli aktivlashtirildi',
                    'email': email,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'phone_number': user.phone_number,
                        'full_name': user.full_name,
                    }
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


class UserLoginView(APIView):
    """
    User login qilish. Email va parol tekshiriladi,
    agar to'g'ri bo'lsa JWT tokenlar qaytariladi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=UserLoginResponseSerializer,
                description='Login muvaffaqiyatli, JWT tokenlar berildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Email yoki parol noto\'g\'ri'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Akkount aktivlashtirilmagan'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Foydalanuvchi topilmadi'
            ),
        },
        tags=['Authentication'],
        summary='Login qilish',
        description='Email va parol bilan login qilib JWT tokenlarni olish'
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)

            # Parolni tekshirish
            if not user.check_password(password):
                return Response(
                    {'error': 'Email yoki parol noto\'g\'ri'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Aktivatsiya tekshiruvi
            if not user.is_active:
                return Response(
                    {'error': 'Akkount aktivlashtirilmagan. Iltimos, emailingizga yuborilgan kodni kiriting'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # JWT tokenlarni generatsiya qilish
            refresh = RefreshToken.for_user(user)

            response_data = {
                'success': True,
                'message': 'Login muvaffaqiyatli',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'full_name': user.full_name,
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'Email yoki parol noto\'g\'ri'},
                status=status.HTTP_400_BAD_REQUEST
            )

