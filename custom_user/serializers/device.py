from rest_framework import serializers
from django.contrib.auth import get_user_model
from custom_user.models import Device
from custom_user.utils import get_device_from_token

User = get_user_model()

class DeviceSerializer(serializers.ModelSerializer):
    me = serializers.SerializerMethodField()
    login_data = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Device
        fields = ('uid', 'device_name', 'device_hardware', 'location_city', 'last_online', 'is_active', 'me', 'login_data')
        read_only_fields = ('uid', 'last_used')

    def get_me(self, obj):
        request = self.context.get('request')

        if request:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_string = auth_header.split(' ')[1]
            else:
                return False

            token_data = get_device_from_token(token_string)
            device_hardware = token_data.get("device_hardware")

            return obj.device_hardware == device_hardware

        return False


class DeviceDeleteResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()