from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    inventory = models.IntegerField(default=1)
    rating = models.SmallIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    class Meta:
        indexes = models.Index(fields=['price']),

    def __str__(self):
        return self.title

