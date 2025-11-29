from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from custom_user.serializers import (
    ErrorResponseSerializer,
    DeviceSerializer,
    DeviceDeleteResponseSerializer,
)
from custom_user.models import Device
from custom_user.utils import get_device_from_token


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


class DeviceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=DeviceSerializer(many=True),
                description='User qurilmalari ro\'yxati'
            ),
        },
        tags=['Devices'],
        summary='Qurilmalar ro\'yxati',
        description='Joriy user\'ning barcha qurilmalarini ko\'rish'
    )
    def get(self, request):
        devices = Device.objects.filter(user=request.user)
        serializer = DeviceSerializer(devices, many=True)

        return Response(
            {
                'success': True,
                'count': devices.count(),
                'devices': serializer.data
            },
            status=status.HTTP_200_OK
        )
