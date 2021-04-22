from django.contrib import admin
from .models import Profile, Order


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'BTC', 'funds']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['_id', 'profile', 'type', 'status']
    list_filter = ['profile', 'type', 'status']