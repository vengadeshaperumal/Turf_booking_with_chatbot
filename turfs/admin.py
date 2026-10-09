
from django.contrib import admin
from .models import Turf


@admin.register(Turf)
class TurfAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "vendor",
        "location",
        "price_per_hour",
        "is_available",
    )
    search_fields = ("name", "location", "vendor__username")
    list_filter = ("is_available",)
