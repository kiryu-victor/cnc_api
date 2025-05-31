from django.urls import path
from .views import operator_panel

urlpatterns = [
    path("operator/", operator_panel, name="operator_panel"),
]