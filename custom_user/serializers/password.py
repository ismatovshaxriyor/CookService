from rest_framework import serializers


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email manzili")


class ForgotPasswordResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=6, min_length=6, required=True, help_text="6 raqamli kod")
    new_password = serializers.CharField(min_length=8, required=True, write_only=True, help_text="Yangi parol")

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak")
        return value


class ResetPasswordResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
