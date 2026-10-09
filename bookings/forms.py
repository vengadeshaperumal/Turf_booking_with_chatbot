
from datetime import date
from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["booking_date", "start_time", "end_time"]

        widgets = {
            "booking_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean_booking_date(self):
        booking_date = self.cleaned_data["booking_date"]

        if booking_date < date.today():
            raise forms.ValidationError("You cannot book a past date.")

        return booking_date

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if start and end and start >= end:
            self.add_error("end_time", "End time must be later than start time.")

        return cleaned_data