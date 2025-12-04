from custom_user.models import Address
from rest_framework import serializers


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('id', 'lat', 'long', 'name', 'address', 'apartment', 'entrance',
                  'floor', 'door_phone', 'instructions', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class AddressCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('lat', 'long', 'name', 'address', 'apartment', 'entrance',
                  'floor', 'door_phone', 'instructions', 'default')

    def validate(self, data):
        if not data.get('address'):
            raise serializers.ValidationError({'address': 'Address majburiy'})
        return data


class AddressUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('lat', 'long', 'name', 'address', 'apartment', 'entrance',
                  'floor', 'door_phone', 'instructions', 'default')