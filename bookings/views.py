
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from turfs.models import Turf
from .forms import BookingForm
from .models import Booking


@login_required
def create_booking(request, turf_id):
    turf = get_object_or_404(Turf, pk=turf_id, is_available=True)

    if request.user.role != User.Role.USER:
        messages.error(request, "Only registered users can book turfs.")
        return redirect("turf_detail", pk=turf.pk)

    form = BookingForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.turf = turf
        booking.user = request.user
        booking.status = Booking.Status.PENDING

        duration = (
            booking.end_time.hour * 60 + booking.end_time.minute
            - booking.start_time.hour * 60 - booking.start_time.minute
        )

        booking.total_price = (
            turf.price_per_hour * Decimal(duration) / Decimal(60)
        )

        try:
            with transaction.atomic():
                booking.full_clean()
                booking.save()

            messages.success(request, "Your booking request was submitted.")
            return redirect("my_bookings")

        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for errors in exc.message_dict.values():
                    for error in errors:
                        form.add_error(None, error)
            else:
                for error in exc.messages:
                    form.add_error(None, error)

    return render(request, "bookings/booking_form.html", {
        "form": form,
        "turf": turf,
    })


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related("turf")
    return render(request, "bookings/my_bookings.html", {
        "bookings": bookings,
    })


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        user=request.user,
    )

    if booking.status == Booking.Status.CANCELLED:
        messages.info(request, "This booking is already cancelled.")
    else:
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        messages.success(request, "Booking cancelled successfully.")

    return redirect("my_bookings")


@login_required
def vendor_bookings(request):
    if request.user.role != User.Role.VENDOR and not request.user.is_superuser:
        messages.error(request, "Vendor access is required.")
        return redirect("dashboard")

    bookings = Booking.objects.select_related("turf", "user")

    if not request.user.is_superuser:
        bookings = bookings.filter(turf__vendor=request.user)

    return render(request, "bookings/vendor_bookings.html", {
        "bookings": bookings,
    })


@login_required
@require_POST
def update_booking_status(request, booking_id):
    if request.user.role != User.Role.VENDOR and not request.user.is_superuser:
        messages.error(request, "Vendor access is required.")
        return redirect("dashboard")

    booking = get_object_or_404(
        Booking.objects.select_related("turf"),
        pk=booking_id,
    )

    if (
        not request.user.is_superuser
        and booking.turf.vendor_id != request.user.id
    ):
        messages.error(request, "You cannot manage another vendor's booking.")
        return redirect("vendor_bookings")

    status = request.POST.get("status")
    allowed_statuses = {
        Booking.Status.CONFIRMED,
        Booking.Status.CANCELLED,
    }

    if status not in allowed_statuses:
        messages.error(request, "Invalid booking status.")
        return redirect("vendor_bookings")

    if status == Booking.Status.CONFIRMED:
        overlapping = Booking.objects.filter(
            turf=booking.turf,
            booking_date=booking.booking_date,
            start_time__lt=booking.end_time,
            end_time__gt=booking.start_time,
        ).exclude( 
            Q(status=Booking.Status.CANCELLED) | Q(pk=booking.pk)
        )

        if overlapping.exists():
            messages.error(
                request,
                "This slot conflicts with another active booking.",
            )
            return redirect("vendor_bookings")

    booking.status = status
    booking.save(update_fields=["status"])
    messages.success(request, "Booking status updated.")
    return redirect("vendor_bookings")
