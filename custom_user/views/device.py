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
                description='Bu device sizga tegishli emas'
            ),
        },
        tags=['Devices'],
        summary='Device o\'chirish',
        description='UID orqali qurilmani o\'chirish'
    )
    def delete(self, request, uid):
        try:
            device = Device.objects.get(uid=uid)

            # Tekshirish: device joriy user'ga tegishli bo'lishi kerak
            if device.user != request.user:
                return Response(
                    {'error': 'Bu qurilma sizga tegishli emas'},
                    status=status.HTTP_403_FORBIDDEN
                )

            device.delete()

            return Response(
                {
                    'success': True,
                    'message': 'Qurilma muvaffaqiyatli o\'chirildi'
                },
                status=status.HTTP_200_OK
            )

        except Device.DoesNotExist:
            return Response(
                {'error': 'Qurilma topilmadi'},
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
