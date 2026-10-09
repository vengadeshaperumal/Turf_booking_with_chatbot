
from django import forms
from .models import Turf


class TurfForm(forms.ModelForm):
    class Meta:
        model = Turf
        fields = [
            "name",
            "location",
            "description",
            "price_per_hour",
            "facilities",
            "opening_time",
            "closing_time",
            "image",
            "is_available",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "facilities": forms.Textarea(attrs={"rows": 3}),
            "opening_time": forms.TimeInput(attrs={"type": "time"}),
            "closing_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        opening = cleaned_data.get("opening_time")
        closing = cleaned_data.get("closing_time")
        price = cleaned_data.get("price_per_hour")

        if opening and closing and opening >= closing:
            self.add_error(
                "closing_time",
                "Closing time must be later than opening time.",
            )

        if price is not None and price <= 0:
            self.add_error(
                "price_per_hour",
                "Price must be greater than zero.",
            )

        return cleaned_data