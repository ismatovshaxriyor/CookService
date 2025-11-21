from django.urls import path, include
from rest_framework.routers import DefaultRouter
from custom_user.views import *

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('activation/send/', SendActivationCodeView.as_view(), name='send-activation-code'),
    path('activation/verify/', VerifyActivationCodeView.as_view(), name='verify-activation-code'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path("me/update_photo/", ProfilePhotoUpdateView.as_view(), name='update-photo'),

    path('', include(router.urls)),

    path('devices/', DeviceListView.as_view(), name='device-list'),
    path('devices/<uuid:uid>/delete/', DeviceDeleteView.as_view(), name='device-delete'),
]