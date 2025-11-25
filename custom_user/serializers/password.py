from rest_framework import serializers


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email manzili")


class ForgotPasswordResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    email = serializers.EmailField()

class ForgotPasswordCompleteSerializer(serializers.Serializer):
    reset_token = serializers.UUIDField(required=True, help_text="Reset token (UUID)")
    new_password = serializers.CharField(min_length=8, required=True, write_only=True, help_text="Yangi parol")


class ForgotPasswordCompleteResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


class VerifyCodeUniversalResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    request_type = serializers.CharField()
    email = serializers.EmailField()
    # Faqat register uchun
    access = serializers.CharField(required=False, help_text="JWT Access Token (faqat register)")
    refresh = serializers.CharField(required=False, help_text="JWT Refresh Token (faqat register)")
    user = serializers.DictField(required=False, help_text="User ma'lumotlari (faqat register)")
    device = serializers.DictField(required=False, help_text="Device ma'lumotlari (faqat register)")
    # Faqat forgot uchun
    reset_token = serializers.UUIDField(required=False, help_text="Reset token UUID (faqat forgot)")

class ResetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(min_length=8, required=True, write_only=True, help_text='Old parol')
    new_password = serializers.CharField(min_length=8, required=True, write_only=True, help_text="New parol")


class ResetPasswordResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
