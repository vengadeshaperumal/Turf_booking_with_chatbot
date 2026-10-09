
from django.conf import settings
from django.db import models


class Turf(models.Model):
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="turfs",
    )
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=255)
    description = models.TextField()
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    facilities = models.TextField(blank=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    image = models.ImageField(
        upload_to="turfs/",
        blank=True,
        null=True,
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
