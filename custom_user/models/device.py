import uuid
from django.db import models
from .user import CustomUser

class Device(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='devices')
    device_ip = models.CharField(max_length=45, null=True, blank=True)
    device_hardware = models.CharField(max_length=100, null=True, blank=True)
    device_name = models.CharField(max_length=100, null=True, blank=True)
    location_city = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_online = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    access_token = models.CharField(max_length=300, null=True, blank=True)
    refresh_token = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'users_device'
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        ordering = ['-last_online']

    def __str__(self):
        return f"{self.user.email} - {self.device_name or 'Unknown Device'}"