import uuid
from django.db import models

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
    order_name = models.CharField(max_length=50)
    order_description = models.TextField(blank=True)
    order_date_creation = models.DateTimeField(auto_now_add=True)
    order_date_completion = models.DateTimeField()
    order_status = models.CharField(
            max_length=20,
            choices=STATUS_POSSIBLE,
            default="pending"
    )

    def __str__(self):
        return self.order_name


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
    machine_name = models.CharField(max_length=50)
    machine_description = models.TextField(blank=True)
    machine_type = models.CharField(max_length=50, choices=TYPE_POSSIBLE)
    machine_status = models.CharField(
            max_length=20,
            choices=STATUS_POSSIBLE,
            default="idle"
    )
    machine_location = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.machine_name


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

    task_id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
    )
    task_order = models.ForeignKey(
            Order,
            on_delete=models.CASCADE,
            related_name="tasks"
    )
    task_machine = models.ForeignKey(
            Machine,
            on_delete=models.CASCADE,
            related_name="tasks",
    )
    task_operation = models.CharField(max_length=50)
    task_queue_number = models.PositiveIntegerField()
    task_status = models.CharField(
            max_length=20,
            choices=STATUS_POSSIBLE,
            default="pending"
    )
    task_start_time = models.DateTimeField(null=True, blank=True)
    task_finish_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["task_queue_number"]

    def __str__(self):
        return f"{self.task_operation} on {self.task_machine.machine_name}"


class ActivityLog(models.Model):
    """Represents an event that has happened during the execution on a task."""
    LOG_POSSIBLE = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
    ]

    log_id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False
    )
    log_task = models.ForeignKey(
            Task,
            on_delete=models.CASCADE,
            related_name="logs"
    )
    log_time = models.DateTimeField(auto_now_add=True)
    log_message = models.TextField()
    log_type = models.CharField(
            max_length=10,
            choices=LOG_POSSIBLE,
            default="info",
    )

    def __str__(self):
        return f"[{self.log_type.upper()}] {self.log_time} - Task {self.log_task.task_id}"