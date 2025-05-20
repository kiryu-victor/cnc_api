from django.contrib import admin
from .models import Order, Machine, Task, ActivityLog

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "date_creation", "date_completion")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("name", "machine_type", "status", "location")
    list_filter = ("machine_type", "status")
    search_fields = ("name", "location")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("operation", "order", "machine", "status", "queue_number")
    list_filter = ("status", "machine")
    search_fields = ("operation",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("task", "time", "log_type")
    list_filter = ("log_type",)
    search_fields = ("message",)