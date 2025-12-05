import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Card(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    name = models.CharField(max_length=100, null=True, blank=True,
                            help_text="Karta nomi (Mening kartam, Ish kartasi...)")
    card_number = models.CharField(max_length=19, unique=True, help_text="Karta raqami (masalan: 8600 1234 5678 9012)")
    card_name = models.CharField(max_length=100, help_text="Karta egasining ismi", default='UzCard')
    card_expiry_date = models.CharField(max_length=5, help_text="Amal qilish muddati (MM/YY)")
    phone_number = models.CharField(max_length=20, null=True, blank=True, help_text="Telefon raqami", default='')
    default = models.BooleanField(default=False, help_text="Asosiy karta")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_card'
        verbose_name = 'Card'
        verbose_name_plural = 'Cards'
        ordering = ['-default', '-created_at']

    def __str__(self):
        masked_number = f"**** **** **** {self.card_number[-4:]}" if len(self.card_number) >= 4 else self.card_number
        return f"{self.user.email} - {masked_number}"

    def save(self, *args, **kwargs):
        if self.default:
            Card.objects.filter(user=self.user, default=True).exclude(pk=self.pk).update(default=False)

        if not self.pk and not Card.objects.filter(user=self.user).exists():
            self.default = True

        super().save(*args, **kwargs)

    @property
    def masked_number(self) -> str:
        if len(self.card_number) >= 4:
            return f"{self.card_number[:4]} **** **** {self.card_number[-4:]}"
        return self.card_number