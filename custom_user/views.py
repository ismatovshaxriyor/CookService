# users/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from djoser.views import UserViewSet
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
    UserLoginResponseSerializer,
    ProfilePhotoSerializer,
    DeviceSerializer,
    DeviceCreateSerializer,
    DeviceCreateResponseSerializer,
    DeviceDeleteResponseSerializer,
)
from .services import get_client_ip
from .models import Device

User = get_user_model()


class UserRegistrationView(APIView):
    """
    Yangi user ro'yxatdan o'tish. User yaratiladi lekin is_active=False bo'ladi.
    Keyin email'ga aktivatsiya kodi yuboriladi.
    IP address bilan ishlaydi - har safar yangi qurilmadan register qilganda
    eski cache bekor qilinadi va yangi kod yuboriladi.
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
        email = request.data.get('email')
        ip_address = get_client_ip(request)

        if email:
            if User.objects.filter(email=email, is_active=True).exists():
                return Response(
                    {'error': 'Bu email allaqachon ro\'yxatdan o\'tgan va aktivlashtirilgan'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            old_user = User.objects.filter(email=email, is_active=False).first()
            if old_user:
                old_cache_key = f'activation_code_{old_user.id}'
                cache.delete(old_cache_key)
                old_user.delete()

        serializer = UserRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()

        email = user.email 

        code = ''.join(random.choices(string.digits, k=6))

        cache_key = f'activation_code_{user.id}'
        cache_data = {
            'email': email,
            'code': code,
            'ip_address': ip_address,
            'user_id': user.id
        }
        cache.set(cache_key, cache_data, timeout=300) 

        try:
            send_mail(
                subject='Aktivatsiya kodi',
                message=f'Assalomu alaykum!\n\nSizning aktivatsiya kodingiz: {code}\n\nKod 5 daqiqa amal qiladi.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
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
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response(
                    {'error': 'Bu akkount allaqachon aktivlashtirilgan'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cache_key = f'activation_code_{user.id}'
            cached_data = cache.get(cache_key)

            if cached_data:
                if cached_data.get('ip_address') == ip_address:
                    last_sent_key = f'last_code_sent_{user.id}_{ip_address}'
                    if cache.get(last_sent_key):
                        return Response(
                            {'error': 'Iltimos, yangi kod so\'rash uchun 1 daqiqa kuting'},
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
            cache.set(cache_key, cache_data, timeout=300)
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
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)

            if not user.check_password(password):
                return Response(
                    {'error': 'Email yoki parol noto\'g\'ri'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not user.is_active:
                return Response(
                    {'error': 'Akkount aktivlashtirilmagan. Iltimos, emailingizga yuborilgan kodni kiriting'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)

            response_data = {
                'success': True,
                'message': 'Login muvaffaqiyatli',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'Email yoki parol noto\'g\'ri'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProfilePhotoUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = ProfilePhotoSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='profile_photo',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True
            )
        ]
    )
    def patch(self, request):
        user = request.user

        photo = request.FILES.get("profile_photo")
        if not photo:
            return Response({"error": "profile_photo is required"}, status=400)

        user.profile_photo = photo
        user.save()

        return Response({"message": "Profile photo updated successfully"})


class CustomUserViewSet(UserViewSet):

    # 🔹 Faqat update (PUT)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    # 🔹 Faqat partial update (PATCH)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    # 🔹 Faqat delete (DELETE)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    # ❌ GET /users/ — o‘chiramiz
    @swagger_auto_schema(auto_schema=None)
    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "List endpoint disabled."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )



    # ❌ POST /users/ — register endpointni ham bloklaymiz
    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Registration disabled."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # ❌ Djoser actionlarini o‘chirib qo‘yamiz
    @swagger_auto_schema(auto_schema=None)
    def reset_password(self, request, *args, **kwargs):
        return Response({"detail": "Disabled."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(auto_schema=None)
    def activation(self, request, *args, **kwargs):
        return Response({"detail": "Disabled."}, status=status.HTTP_404_NOT_FOUND)


class DeviceCreateView(APIView):
    """
    Authenticated user uchun yangi device yaratish.
    IP address avtomatik olinadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=DeviceCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=DeviceCreateResponseSerializer,
                description='Device muvaffaqiyatli yaratildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Validatsiya xatosi'
            ),
        },
        tags=['Devices'],
        summary='Yangi device qo\'shish',
        description='Joriy user uchun yangi qurilma qo\'shish'
    )
    def post(self, request):
        serializer = DeviceCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # IP address avtomatik olish
        ip_address = get_client_ip(request)

        # Device yaratish
        device = Device.objects.create(
            user=request.user,
            device_ip=ip_address,
            device_hardware=serializer.validated_data.get('device_hardware', ''),
            device_name=serializer.validated_data.get('device_name', ''),
            location_city=serializer.validated_data.get('location_city', ''),
        )

        response_data = {
            'success': True,
            'message': 'Qurilma muvaffaqiyatli qo\'shildi',
            'device': DeviceSerializer(device).data
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class DeviceDeleteView(APIView):
    """
    Device'ni o'chirish (faqat o'z device'larini o'chirishi mumkin)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=DeviceDeleteResponseSerializer,
                description='Device muvaffaqiyatli o\'chirildi'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Device topilmadi'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Bu device sizga tegishli emas'
            ),
        },
        tags=['Devices'],
        summary='Device o\'chirish',
        description='UID orqali qurilmani o\'chirish'
    )
    def delete(self, request, uid):
        try:
            device = Device.objects.get(uid=uid)

            # Tekshirish: device joriy user'ga tegishli bo'lishi kerak
            if device.user != request.user:
                return Response(
                    {'error': 'Bu qurilma sizga tegishli emas'},
                    status=status.HTTP_403_FORBIDDEN
                )

            device.delete()

            return Response(
                {
                    'success': True,
                    'message': 'Qurilma muvaffaqiyatli o\'chirildi'
                },
                status=status.HTTP_200_OK
            )

        except Device.DoesNotExist:
            return Response(
                {'error': 'Qurilma topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )


class DeviceListView(APIView):
    """
    Joriy user'ning barcha qurilmalarini ko'rish (bonus)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=DeviceSerializer(many=True),
                description='User qurilmalari ro\'yxati'
            ),
        },
        tags=['Devices'],
        summary='Qurilmalar ro\'yxati',
        description='Joriy user\'ning barcha qurilmalarini ko\'rish'
    )
    def get(self, request):
        devices = Device.objects.filter(user=request.user)
        serializer = DeviceSerializer(devices, many=True)

        return Response(
            {
                'success': True,
                'count': devices.count(),
                'devices': serializer.data
            },
            status=status.HTTP_200_OK
        )

