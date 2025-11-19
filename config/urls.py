# urls.py (asosiy loyiha papkasidagi urls.py)
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from custom_user.views import UserRegistrationView, SendActivationCodeView, VerifyActivationCodeView, UserLoginView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # Custom authentication endpoints
    path('api/auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/auth/activation/send/', SendActivationCodeView.as_view(), name='send-activation-code'),
    path('api/auth/activation/verify/', VerifyActivationCodeView.as_view(), name='verify-activation-code'),
    path('api/auth/login/', UserLoginView.as_view(), name='user-login'),
    
    # JWT endpoints (faqat login va refresh uchun)
    path('api/auth/', include('djoser.urls.jwt')),
    
    # Swagger/OpenAPI documentation URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]