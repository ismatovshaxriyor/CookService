import uuid
from django.db import models
from custom_user.models import CustomUser

class Location(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='location')
    name = models.CharField(max_length=50, null=True)
    city = models.CharField(max_length=25, null=True)
    latitude = models.FloatField(null=False)
    longitude = models.FloatField(null=False)

    def __str__(self):
        return f"{self.user.full_name} - {self.name}"
