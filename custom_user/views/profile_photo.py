from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from custom_user.serializers import (
    ProfilePhotoSerializer,
)

User = get_user_model()

class ProfilePhotoUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = ProfilePhotoSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='profile_photo',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True
            )
        ]
    )
    def patch(self, request):
        user = request.user

        photo = request.FILES.get("profile_photo")
        if not photo:
            return Response({"error": "profile_photo is required"}, status=400)

        user.profile_photo = photo
        user.save()

        return Response({"message": "Profile photo updated successfully"})
