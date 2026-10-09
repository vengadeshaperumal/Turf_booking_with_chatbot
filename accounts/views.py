
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import RegisterForm, VendorRegisterForm, LoginForm
from .models import User


def home(request):
    return render(request, "home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account was created successfully.")
        return redirect("dashboard")

    return render(request, "accounts/register.html", {"form": form})


def vendor_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = VendorRegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.role = User.Role.VENDOR
        user.save()
        login(request, user)
        messages.success(request, "Vendor account created successfully.")
        return redirect("dashboard")

    return render(request, "accounts/register.html", {
        "form": form,
        "vendor_registration": True,
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("dashboard")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def dashboard(request):
    if request.user.is_superuser or request.user.role == User.Role.ADMIN:
        return redirect("/admin/")

    if request.user.role == User.Role.VENDOR:
        return render(request, "accounts/dashboard.html", {
            "dashboard_role": "Vendor",
        })

    return render(request, "accounts/dashboard.html", {
        "dashboard_role": "User",
    })


@login_required
@require_POST
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")