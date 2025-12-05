from django.db import models
from .restaurants import Restaurants

class RestaurantBranches(models.Model):
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255, db_index=True)
