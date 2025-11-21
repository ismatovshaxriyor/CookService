from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class SendActivationCodeSerializer(serializers.Serializer):
    """Aktivatsiya kodini yuborish uchun serializer"""
    email = serializers.EmailField(
        required=True,
        help_text="Foydalanuvchi email manzili"
    )


class SendActivationCodeResponseSerializer(serializers.Serializer):
    """Aktivatsiya kodi yuborilgandan keyin response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    email = serializers.EmailField()

class VerifyActivationCodeSerializer(serializers.Serializer):
    """Aktivatsiya kodini tekshirish uchun serializer"""
    email = serializers.EmailField(
        required=True,
        help_text="Foydalanuvchi email manzili"
    )
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True,
        help_text="6 raqamli aktivatsiya kodi"
    )
    device_hardware = serializers.CharField()

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak")
        return value


class VerifyActivationCodeResponseSerializer(serializers.Serializer):
    """Aktivatsiya muvaffaqiyatli bo'lgandan keyin JWT tokenlar bilan response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    access = serializers.CharField(help_text="JWT Access Token")
    refresh = serializers.CharField(help_text="JWT Refresh Token")

