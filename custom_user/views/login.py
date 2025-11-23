from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.tokens import RefreshToken

from custom_user.models import Device
from custom_user.serializers import (
    ErrorResponseSerializer,
    UserLoginSerializer,
    UserLoginResponseSerializer,
)
from custom_user.services import get_device_info, get_location_by_ip, get_client_ip

User = get_user_model()

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=UserLoginResponseSerializer,
                description='Login muvaffaqiyatli, JWT tokenlar berildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Email yoki parol noto\'g\'ri'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Akkount aktivlashtirilmagan'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Foydalanuvchi topilmadi'
            ),
        },
        tags=['Authentication'],
        summary='Login qilish',
        description='Email va parol bilan login qilib JWT tokenlarni olish'
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            first_field = next(iter(errors))
            error_msg = errors[first_field][0]

            return Response(
                {'success': False, 'error': error_msg, 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        device_hardware = serializer.validated_data['device_hardware']
        ip_address = get_client_ip(request)
        location_city = get_location_by_ip(ip_address)
        device = get_device_info(request)
        device_model = device.get("device_model")


        try:
            user = User.objects.get(email=email)

            if not user.check_password(password):
                return Response(
                    {'success': False, 'error': 'Incorrect email or password', 'errorStatus': 'data_credential'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not user.is_active:
                return Response(
                    {'succes': False, 'error': 'Account not actvated', 'errorStatus': 'unauthorized'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            new_device, created = Device.objects.get_or_create(
                user=user,
                device_hardware=device_hardware,
                defaults={"device_name": device_model, "locations_city": location_city}
            )

            message = "Login successfull"
            if created:
                message += 'New device detected'
            else:
                return Response(
                    {
                        'success': False,
                        'error': "This device is already exists",
                        'errorStatus': 'exists'
                    }
                )


            refresh = RefreshToken.for_user(user)

            response_data = {
                'success': True,
                'message': message,
                'login_response': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Incorrect email or password', 'errorStatus': 'data_credential'},
                status=status.HTTP_400_BAD_REQUEST
            )

