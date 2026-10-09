
from django.urls import path
from . import views

urlpatterns = [
    path("create/<int:turf_id>/", views.create_booking, name="create_booking"),
    path("my/", views.my_bookings, name="my_bookings"),
    path("cancel/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("vendor/", views.vendor_bookings, name="vendor_bookings"),
    path(
        "vendor/update/<int:booking_id>/",
        views.update_booking_status,
        name="update_booking_status",
    ),
]