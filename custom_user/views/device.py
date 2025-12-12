from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from custom_user.serializers import (
    ErrorResponseSerializer,
    DeviceSerializer,
    DeviceDeleteResponseSerializer,
)
from custom_user.models import Device
from custom_user.utils import get_device_from_token
from custom_user.pagination import CustomPageNumberPagination


class DeviceDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=DeviceDeleteResponseSerializer,
                description='Device muvaffaqiyatli o\'chirildi'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Device topilmadi'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Bu device sizga tegishli emas yoki token noto\'g\'ri'
            ),
        },
        tags=['Devices'],
        summary='Device o\'chirish (token orqali)',
        description='JWT token orqali device\'ni o\'chirish - UUID kerak emas'
    )
    def delete(self, request):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return Response(
                {'success': False, 'error': 'Token not found', 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = auth_header.split(' ')[1]

        token_data = get_device_from_token(token)

        if not token_data:
            return Response(
                {'success': False, 'error': 'Invalid or expired token', 'errorStatus': 'invalid_token'},
                status=status.HTTP_403_FORBIDDEN
            )

        device_hardware = token_data.get('device_hardware')
        token_user_id = token_data.get('user_id')

        if not device_hardware:
            return Response(
                {'success': False, 'error': 'The token does not contain device information.', 'errorStatus': 'invalid_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if int(token_user_id) != request.user.id:
            return Response(
                {'success': False, 'error': 'This device does not belong to you.', 'errorStatus': 'data_credential'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            device = Device.objects.get(
                user=request.user,
                device_hardware=device_hardware
            )

            device.delete()

            return Response(
                {
                    'success': True,
                    'message': 'Device successfully deleted.',
                },
                status=status.HTTP_200_OK
            )

        except Device.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Device not found', 'errorStatus': 'exists'},
                status=status.HTTP_404_NOT_FOUND
            )

class DeviceDeleteWithUidView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uid):
        try:
            return Device.objects.get(uid=uid, user=self.request.user)
        except Device.DoesNotExist:
            return None

    @extend_schema(
        responses={
            200: OpenApiResponse(description='Device o\'chirildi'),
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        },
        tags=['Devices'],
        summary='Device uid bilan o\'chirish'
    )
    def delete(self, request, uid):
        device = self.get_object(uid)

        if not device:
            return Response(
                {
                    'success': False,
                    'error': 'Device not found',
                    'errorStatus': 'data_credential'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        device.delete()

        return Response(
            {
                'success': True,
                'message': 'Device deleted successfully.'
            }
        )


class DeviceListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # me bo'yicha tartiblash: True'lar birinchi
        sorted_data = sorted(
            serializer.data,
            key=lambda x: x.get('me', False),
            reverse=True
        )

        # Pagination
        page = self.paginate_queryset(sorted_data)
        if page is not None:
            return self.get_paginated_response(page)

        return Response(sorted_data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='page', description='Sahifa raqami', required=False, type=int),
            OpenApiParameter(name='page_size', description='Sahifadagi elementlar soni (max: 100)', required=False,
                             type=int, default=5),
        ],
        responses={200: DeviceSerializer(many=True)},
        tags=['Devices'],
        summary='Qurilmalar ro\'yxati',
        description='Joriy user\'ning barcha qurilmalarini ko\'rish'
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


