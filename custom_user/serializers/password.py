from rest_framework import serializers


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email manzili")


class ForgotPasswordResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email manzili")
    old_password = serializers.CharField(required=True, write_only=True, help_text="Eski parol")
    new_password = serializers.CharField(min_length=8, required=True, write_only=True, help_text="Yangi parol")


class ResetPasswordResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
