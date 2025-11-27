from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude")
    long = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude")
    name = models.CharField(max_length=100, null=True, blank=True, help_text="Manzil nomi (Uy, Ish, ...)")
    address = models.CharField(max_length=255, help_text="To'liq manzil")
    apartment = models.CharField(max_length=50, null=True, blank=True, help_text="Kvartira raqami")
    entrance = models.CharField(max_length=50, null=True, blank=True, help_text="Kirish")
    floor = models.CharField(max_length=50, null=True, blank=True, help_text="Qavat")
    door_phone = models.CharField(max_length=50, null=True, blank=True, help_text="Domofon kodi")
    instructions = models.TextField(null=True, blank=True, help_text="Qo'shimcha ko'rsatmalar")
    default = models.BooleanField(default=False, help_text="Asosiy manzil")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_address'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        ordering = ['-default', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.name or self.address}"

    def save(self, *args, **kwargs):
        if self.default:
            Address.objects.filter(user=self.user, default=True).exclude(pk=self.pk).update(default=False)

        if not self.pk and not Address.objects.filter(user=self.user).exists():
            self.default = True

        super().save(*args, **kwargs)