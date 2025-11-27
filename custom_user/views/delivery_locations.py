from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from custom_user.serializers import (
    AddressSerializer,
    AddressCreateSerializer,
    AddressUpdateSerializer,
    ErrorResponseSerializer
)
from custom_user.models import Address


class AddressListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="address_list",
        responses={
            200: OpenApiResponse(
                response=AddressSerializer(many=True),
                description='Manzillar ro\'yxati'
            ),
        },
        tags=['Addresses'],
        summary='Manzillar ro\'yxati',
        description='User\'ning barcha manzillari (default birinchi)'
    )
    def get(self, request):
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)

        return Response({
            'success': True,
            'count': addresses.count(),
            'addresses': serializer.data
        }, status=status.HTTP_200_OK)


class AddressCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddressCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=AddressSerializer,
                description='Manzil muvaffaqiyatli yaratildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Validatsiya xatosi'
            ),
        },
        tags=['Addresses'],
        summary='Yangi manzil qo\'shish',
        description='User uchun yangi manzil yaratish'
    )
    def post(self, request):
        serializer = AddressCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': serializer.errors, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        address = serializer.save(user=request.user)

        return Response({
            'success': True,
            'message': 'Address added successfully.',
        }, status=status.HTTP_201_CREATED)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, address_id):
        try:
            return Address.objects.get(id=address_id, user=self.request.user)
        except Address.DoesNotExist:
            return None

    @extend_schema(
        operation_id="address_detail",
        responses={
            200: AddressSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Addresses'],
        summary='Manzilni ko\'rish',
    )
    def get(self, request, address_id):
        address = self.get_object(address_id)

        if not address:
            return Response(
                {'success': False, 'error': 'Address not found', 'errorStatus': 'data_credential'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'success': True,
            'address': AddressSerializer(address).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=AddressUpdateSerializer,
        responses={
            200: AddressSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Addresses'],
        summary='Manzilni yangilash',
        description='Partial update - faqat yuborilgan fieldlar yangilanadi'
    )
    def patch(self, request, address_id):
        address = self.get_object(address_id)

        if not address:
            return Response(
                {'success': False, 'error': 'Address not found', 'errorStatus': 'data_credential'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AddressUpdateSerializer(address, data=request.data, partial=True)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]

            return Response(
                {'success': False, 'error': error_msg, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response({
            'success': True,
            'message': 'Address updated',
        }, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(description='Manzil o\'chirildi'),
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Addresses'],
        summary='Manzilni o\'chirish',
    )
    def delete(self, request, address_id):
        address = self.get_object(address_id)

        if not address:
            return Response(
                {'success': False, 'error': 'Address not found', 'errorStatus': 'data_credential'},
                status=status.HTTP_404_NOT_FOUND
            )

        was_default = address.default
        address.delete()

        if was_default:
            next_address = Address.objects.filter(user=request.user).first()
            if next_address:
                next_address.default = True
                next_address.save()

        return Response({
            'success': True,
            'message': 'Address deleted.'
        }, status=status.HTTP_200_OK)


class AddressSetDefaultView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    @extend_schema(
        operation_id="address_set_default",
        responses={
            200: AddressSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Addresses'],
        summary='Asosiy manzil qilish',
        description='Tanlangan manzilni default (asosiy) qilish'
    )
    def post(self, request, address_id):
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Address not found', 'errorStatus': 'data_credential'},
                status=status.HTTP_404_NOT_FOUND
            )

        address.default = True
        address.save()

        return Response({
            'success': True,
            'message': 'Primary address changed',
        }, status=status.HTTP_200_OK)