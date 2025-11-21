from rest_framework import serializers
from django.contrib.auth import get_user_model
from custom_user.models import Device

User = get_user_model()

class DeviceSerializer(serializers.ModelSerializer):
    """Device ma'lumotlarini ko'rsatish uchun"""
    class Meta:
        model = Device
        fields = ('uid', 'device_ip', 'device_hardware', 'device_name', 'location_city', 'created_at', 'last_used', 'is_active')
        read_only_fields = ('uid', 'created_at', 'last_used')



class DeviceDeleteResponseSerializer(serializers.Serializer):
    """Device o'chirilgandan keyin response"""
    success = serializers.BooleanField()
    message = serializers.CharField()