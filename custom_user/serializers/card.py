from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from custom_user.models import Card

class CardSerializer(serializers.ModelSerializer):
    """Card ma'lumotlarini ko'rsatish (masked number bilan)"""

    masked_number = serializers.CharField(read_only=True)

    class Meta:
        model = Card
        fields = ('uid', 'name', 'card_number', 'masked_number', 'card_name',
                  'card_expiry_date', 'phone_number', 'created_at', 'updated_at')
        read_only_fields = ('uid', 'masked_number', 'created_at', 'updated_at')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('card_number', None)
        return data


class CardCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Card
        fields = ('name', 'card_number', 'card_name', 'card_expiry_date', 'phone_number', 'default')

    def validate_card_number(self, value):
        cleaned = value.replace(' ', '')
        if not cleaned.isdigit():
            raise serializers.ValidationError("Karta raqami faqat raqamlardan iborat bo'lishi kerak")
        if len(cleaned) < 16:
            raise serializers.ValidationError("Karta raqami kamida 16 ta raqam bo'lishi kerak")
        return value

    def validate_card_expiry_date(self, value):
        # MM/YY formatda bo'lishi kerak
        if len(value) != 5 or value[2] != '/':
            raise serializers.ValidationError("Format: MM/YY")
        month, year = value.split('/')
        if not (month.isdigit() and year.isdigit()):
            raise serializers.ValidationError("MM va YY raqam bo'lishi kerak")
        if not (1 <= int(month) <= 12):
            raise serializers.ValidationError("Oy 01 dan 12 gacha bo'lishi kerak")
        return value


class CardUpdateSerializer(serializers.ModelSerializer):
    """Card'ni yangilash"""

    class Meta:
        model = Card
        fields = ('name', 'card_name', 'card_expiry_date', 'phone_number', 'default')