from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ("id", "email", "phone_number", "full_name", "profile_photo")
        read_only_fields = ("id",)

class ProfilePhotoSerializer(serializers.Serializer):
    profile_photo = serializers.ImageField()

class SendMailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    error = serializers.CharField()
    errorStatus = serializers.CharField()


class VerifyActivationCodeSerializer(serializers.Serializer):
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

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak")
        return value


class VerifyCodeUniversalSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email")
    code = serializers.CharField(max_length=6, min_length=6, required=True, help_text="6 raqamli kod")
    request_type = serializers.ChoiceField(
        choices=['register', 'forgot'],
        required=True,
        help_text="'register' yoki 'forgot'"
    )
    device_hardware = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Qurilma nomi (faqat register uchun)"
    )

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak")
        return value

    def validate(self, data):
        if data['request_type'] == 'register':
            if not data.get('device_hardware'):
                pass
        return data


class VerifyCodeUniversalResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()

    # Faqat register uchun
    access = serializers.CharField(required=False, help_text="JWT Access Token (faqat register)")
    refresh = serializers.CharField(required=False, help_text="JWT Refresh Token (faqat register)")
