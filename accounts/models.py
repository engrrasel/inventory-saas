from django.contrib.auth.models import AbstractUser
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class User(AbstractUser):
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,   # 🔥 safer
        null=True,
        blank=True
    )

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='admin'
    )

    def __str__(self):
        return self.username