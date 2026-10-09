
from django.urls import path
from . import views

urlpatterns = [
    path("", views.turf_list, name="turf_list"),
    path("add/", views.turf_create, name="turf_create"),
    path("<int:pk>/", views.turf_detail, name="turf_detail"),
    path("<int:pk>/edit/", views.turf_update, name="turf_update"),
    path("<int:pk>/delete/", views.turf_delete, name="turf_delete"),
]