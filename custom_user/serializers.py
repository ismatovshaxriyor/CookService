from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True, allow_null=True)
    full_name = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'phone_number', 'full_name', 'password')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            full_name=validated_data.get('full_name', ''),
            is_active=False
        )
        return user


class UserRegistrationResponseSerializer(serializers.Serializer):
    """Register response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    email = serializers.EmailField()


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

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak")
        return value


class VerifyActivationCodeResponseSerializer(serializers.Serializer):
    """Aktivatsiya muvaffaqiyatli bo'lgandan keyin JWT tokenlar bilan response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    email = serializers.EmailField()
    access = serializers.CharField(help_text="JWT Access Token")
    refresh = serializers.CharField(help_text="JWT Refresh Token")
    user = serializers.DictField(help_text="User ma'lumotlari")


class ErrorResponseSerializer(serializers.Serializer):
    """Xatoliklar uchun response"""
    error = serializers.CharField()


class UserLoginSerializer(serializers.Serializer):
    """User login uchun serializer"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)


class UserLoginResponseSerializer(serializers.Serializer):
    """Login muvaffaqiyatli bo'lgandan keyin response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    access = serializers.CharField(help_text="JWT Access Token")
    refresh = serializers.CharField(help_text="JWT Refresh Token")
    user = serializers.DictField(help_text="User ma'lumotlari")