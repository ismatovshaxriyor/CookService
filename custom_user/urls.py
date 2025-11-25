from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from custom_user.views import *
from django.conf import settings

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('activation/send/', SendActivationCodeView.as_view(), name='send-activation-code'),
    path('verify/', VerifyCodeUniversalView.as_view(), name='verify-activation-code'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path("me/update_photo/", ProfilePhotoUpdateView.as_view(), name='update-photo'),
    path('me/notification/', NotificationSettingsView.as_view(), name='update_notification'),

    path('password/forgot/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('password/forgot/complete/', ForgotPasswordCompleteView.as_view(), name='forgot-password-complete'),
    path('password/reset/', ResetPasswordView.as_view(), name='reset-password'),

    path('', include(router.urls)),

    path('devices/', DeviceListView.as_view(), name='device-list'),
    path('devices/<uuid:uid>/delete/', DeviceDeleteView.as_view(), name='device-delete'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)