from django.contrib import admin
from custom_user.models import *


admin.site.register([CustomUser, Card, Address, Device])