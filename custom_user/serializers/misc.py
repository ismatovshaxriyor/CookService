from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ("id", "email", "phone_number", "full_name")
        read_only_fields = ("id",)

class ProfilePhotoSerializer(serializers.Serializer):
    profile_photo = serializers.ImageField()

class SendMailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    error = serializers.CharField()
    errorStatus = serializers.CharField()