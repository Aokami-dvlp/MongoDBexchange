from django.db import models
from django.conf import settings
from djongo.models.fields import ObjectIdField


class Profile(models.Model):
    _id = ObjectIdField()
    username = models.CharField(max_length=150)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    BTC = models.FloatField()
    pending_BTC = models.FloatField()
    funds = models.FloatField()
    pending_funds = models.FloatField()
    profit = models.FloatField()

    def __str__(self):
        return {self.user}

#Extra: custom model managers to manage different statuses and types of order
class BuyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='buy')

class SellManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='sell')

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='active')


class Order(models.Model):
    TYPE_CHOICES = (
        ('buy','buy'),
        ('sell','sell'),
    )

    STATUS_CHOICES = (
        ('active','active'),
        ('completed','completed'),
    )

    _id = ObjectIdField()
    username = models.CharField(max_length=150)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    quantity = models.FloatField()
    type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    objects = models.Manager()
    sell = SellManager()
    buy = BuyManager()
    active = ActiveManager()

    class Meta:
        ordering = ('-datetime',)
