
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from turfs.models import Turf


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    turf = models.ForeignKey(
        Turf,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=models.F("start_time")),
                name="booking_end_after_start",
            ),
        ]

    def clean(self):
        super().clean()

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be later than start time.")

        if self.turf_id and self.booking_date:
            if not self.turf.is_available:
                raise ValidationError("This turf is not currently available.")

            if (
                self.start_time < self.turf.opening_time
                or self.end_time > self.turf.closing_time
            ):
                raise ValidationError(
                    "The booking must be within the turf's opening hours."
                )

            overlapping = Booking.objects.filter(
                turf_id=self.turf_id,
                booking_date=self.booking_date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(status=self.Status.CANCELLED)

            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    "This time slot overlaps with an existing booking."
                )

    def __str__(self):
        return f"{self.turf.name} - {self.booking_date} - {self.user.username}"
