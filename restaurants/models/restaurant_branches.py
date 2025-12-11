from django.db import models
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from .restaurants import Restaurants, phone_regex

class RestaurantBranches(models.Model):
    STATE_CHOICES = [
        ('open', 'open'),
        ('close', 'close')
    ]

    STATUS_CHOICES = [
        ('work', 'work'),
        ('close', 'close')
    ]

    PAYMENT_TYPE_CHOICES = [
        ('stable', 'stable'),
        ('card', 'card')
    ]

    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255, db_index=True)
    banner = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField()
    email = models.EmailField()
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=13, validators=[phone_regex], null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    delivery_time = models.IntegerField(null=True) # in minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurant_branches'
        verbose_name = "Restaurant Branch"
        verbose_name_plural = "Restaurant Branches"
        ordering = ['name', 'restaurant', 'state', 'status']

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def clean(self):
        if self.start_time and self.close_time:
            if self.start_time >= self.close_time:
                raise ValidationError("Closing time must be later than opening time.")

    def __str__(self):
        return self.name


