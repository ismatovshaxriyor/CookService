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
    path('devices/delete/', DeviceDeleteView.as_view(), name='device-delete'),

    path('api/cards/', CardListView.as_view(), name='card-list'),
    path('api/cards/create/', CardCreateView.as_view(), name='card-create'),
    path('api/cards/<uuid:uid>/', CardDetailView.as_view(), name='card-detail'),
    path('api/cards/<uuid:uid>/set-default/', CardSetDefaultView.as_view(), name='card-set-default'),

    path('addresses/', AddressListView.as_view(), name='addresses-list'),
    path('addresses/create', AddressCreateView.as_view(), name='address-create'),
    path('addresses/<int:address_id>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:address_id>/set-default', AddressSetDefaultView.as_view(), name='address-set-default')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)