from rest_framework import serializers
from django.contrib.auth import get_user_model

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



