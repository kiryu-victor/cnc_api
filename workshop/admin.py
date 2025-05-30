from django.contrib import admin
from .models import Order, Machine, Task, ActivityLog

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("name", "order_id", "status", "date_creation", "date_start", "date_completion")
    list_filter = ("status",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("name", "machine_type", "status", "location", "last_maintenance", "next_maintenance")
    list_filter = ("machine_type", "status")
    search_fields = ("name", "location")
    ordering = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("operation", "order", "required_machine_type", "machine", "status", "queue_number")
    list_filter = ("status", "machine")
    search_fields = ("operation",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("time", "log_type", "task", "message", "user")
    list_filter = ("log_type", "time")
    search_fields = ("message",)
    ordering = ("-time",)