import uuid

from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Order(models.Model):
    """Represents an order that implies some tasks to be completed."""
    STATUS_POSSIBLE = [
        ("pending", "Pending"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # Attributes
    order_id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
    )
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_start = models.DateTimeField(blank=True, null=True)
    date_completion = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
            max_length=20,
            choices=STATUS_POSSIBLE,
            default="pending"
    )

    def __str__(self):
        return self.name


class Machine(models.Model):
    """Represents a machine or tool that is used on the workshop."""
    TYPE_POSSIBLE = [
        ("lathe", "Lathe"),
        ("mill", "Mill"),
        ("grinder", "Grinder"),
        ("other", "Other"),
    ]

    STATUS_POSSIBLE = [
        ("idle", "Idle"),
        ("running", "Running"),
        ("maintenance", "Maintenance"),
        ("error", "Error"),
    ]

    # Attributes
    machine_id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,       
    )
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    machine_type = models.CharField(max_length=50, choices=TYPE_POSSIBLE)
    status = models.CharField(
            max_length=20,
            choices=STATUS_POSSIBLE,
            default="idle"
    )
    location = models.CharField(max_length=50, blank=True)

    # Maintenance - When was the last one and when is going to be the next
    # A new machine will be on point coming from the manufacturer
    last_maintenance = models.DateField(auto_now_add=True)
    maintenance_gap_days = models.PositiveIntegerField(default=10)

    @property
    def next_maintenance(self):
        return self.last_maintenance + timedelta(days=self.maintenance_gap_days)
    
    @property
    def needs_maintenance(self):
        maintenance_date = self.next_maintenance
        if timezone.now().date() >= maintenance_date:
            self.status = "maintenance"
            return True
        return False

    def __str__(self):
        return self.name


class Task(models.Model):
    """
    Represents each individual operation that needs to be done
    for an order to be completed.
    """
    STATUS_POSSIBLE = [
        ("pending", "Pending"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    # Attributes
    task_id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
    )
    order = models.ForeignKey(
            Order,
            on_delete=models.CASCADE,
            related_name="tasks"
    )
    required_machine_type = models.CharField(
            max_length=20,
            choices=Machine.TYPE_POSSIBLE,
            default="lathe"
    )
    machine = models.ForeignKey(
            Machine,
            on_delete=models.CASCADE,
            blank=True,
            null=True,
            related_name="tasks",
    )
    operation = models.CharField(max_length=50)
    queue_number = models.PositiveIntegerField()
    status = models.CharField(
            max_length=20,
            choices=STATUS_POSSIBLE,
            default="pending"
    )
    start_time = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["queue_number"]

    def __str__(self):
        return f"{self.operation}"


class ActivityLog(models.Model):
    """Represents an event that has happened during the execution of a task."""
    LOG_POSSIBLE = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
    ]

    # Attributes
    log_id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False
    )
    task = models.ForeignKey(
            Task,
            on_delete=models.CASCADE,
            related_name="logs",
            null=True,
            blank=True
    )
    time = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    log_type = models.CharField(
            max_length=10,
            choices=LOG_POSSIBLE,
            default="info",
    )
    user = models.ForeignKey(
                        User,
                        on_delete=models.SET_NULL,
                        null=True,
                        blank=True
    )

    def __str__(self):
        # If there is a task, get the task_id
        task = self.task.task_id if self.task else None
        return f"[{self.log_type.upper()}] - {self.time} - Task: {task}"