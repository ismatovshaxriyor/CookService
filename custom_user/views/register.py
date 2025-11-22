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
    UserRegistrationSerializer,
    UserRegistrationResponseSerializer,
    ErrorResponseSerializer,
)
from custom_user.services import get_client_ip

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
        cache.set(cache_key, cache_data, timeout=200)

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

