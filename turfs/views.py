
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect

from accounts.models import User
from .models import Turf
from .forms import TurfForm


def turf_list(request):
    turfs = Turf.objects.filter(is_available=True)

    query = request.GET.get("q", "").strip()
    if query:
        turfs = turfs.filter(
            Q(name__icontains=query) |
            Q(location__icontains=query) |
            Q(facilities__icontains=query)
        )

    paginator = Paginator(turfs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "turfs/turf_list.html", {
        "page_obj": page_obj,
        "query": query,
    })


def turf_detail(request, pk):
    turf = get_object_or_404(Turf, pk=pk)
    return render(request, "turfs/turf_detail.html", {"turf": turf})


def vendor_required(view_func):
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if (
            request.user.role != User.Role.VENDOR
            and not request.user.is_superuser
        ):
            messages.error(request, "Vendor access is required.")
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


@vendor_required
def turf_create(request):
    form = TurfForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        turf = form.save(commit=False)
        turf.vendor = request.user
        turf.save()
        messages.success(request, "Turf added successfully.")
        return redirect("turf_list")

    return render(request, "turfs/turf_form.html", {
        "form": form,
        "title": "Add Turf",
    })


@vendor_required
def turf_update(request, pk):
    turf = get_object_or_404(Turf, pk=pk)

    if not request.user.is_superuser and turf.vendor_id != request.user.id:
        messages.error(request, "You cannot edit another vendor's turf.")
        return redirect("turf_list")

    form = TurfForm(
        request.POST or None,
        request.FILES or None,
        instance=turf,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Turf updated successfully.")
        return redirect("turf_detail", pk=turf.pk)

    return render(request, "turfs/turf_form.html", {
        "form": form,
        "title": "Update Turf",
    })


@vendor_required
def turf_delete(request, pk):
    turf = get_object_or_404(Turf, pk=pk)

    if not request.user.is_superuser and turf.vendor_id != request.user.id:
        messages.error(request, "You cannot delete another vendor's turf.")
        return redirect("turf_list")

    if request.method == "POST":
        turf.delete()
        messages.success(request, "Turf deleted successfully.")
        return redirect("turf_list")

    return render(request, "turfs/turf_confirm_delete.html", {
        "turf": turf,
    })
