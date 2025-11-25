from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from custom_user.serializers import NotificationSettingsSerializer, ErrorResponseSerializer, NotificationSettingsResponseSerializer

class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=NotificationSettingsSerializer,
        responses={
            200: OpenApiResponse(
                response=NotificationSettingsResponseSerializer,
                description='Sozlamalar muvaffaqiyatli o\'zgartirildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Validatsiya xatosi'
            ),
        },
        tags=['User Settings'],
        summary='Notification sozlamalari',
        description='User notification sozlamalarini o\'zgartirish (partial update)'
    )
    def patch(self, request):
        serializer = NotificationSettingsSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]

            return Response(
                {'success': False, 'error': error_msg, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        updated_fields = []

        if 'notification' in serializer.validated_data:
            user.notification = serializer.validated_data['notification']
            updated_fields.append('notification')

        if 'promotional_notification' in serializer.validated_data:
            user.promotional_notification = serializer.validated_data['promotional_notification']
            updated_fields.append('promotional_notification')

        user.save()

        response_data = {
            'success': True,
            'message': f"{', '.join(updated_fields)} settings updated.",
        }

        return Response(response_data, status=status.HTTP_200_OK)
