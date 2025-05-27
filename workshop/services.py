from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Machine, ActivityLog

# Machine
def start_task_with_auto_machine_assignation(task):
    """
    Start a task.
    Checks it is "pending".
    Assigns an "idle" machine of the required type.
    Updates the task and machine status.
    Updates the order status if needed if it's the first tasks.
    """

    if task.status != "pending":
        raise ValidationError('Only tasks with "pending" status can be started.')
    
    if not task.machine:
        # Look into the machines with "idle" status and that match the type required
        available_machines = get_available_machines(task)
        # Get the machines that don't need maintenance
        available_machines = [m for m in available_machines if not m.needs_maintenance]
        
        if not available_machines:
            raise ValidationError("No machines of the required type available.")
        
        # Assign a machine, change it status, save it
        machine = available_machines[0]
        task.machine = machine
        machine.status = "running"
        machine.save()

    # Now the task can start
    task.status = "in_progress"
    task.start_time = timezone.now()
    task.save()

    # If this is the first task of an order, change the order status
    if task.order.status == "pending":
        task.order.status = "in_progress"
        task.order.save()

    return task

def get_available_machines(task):
    """
    Get the machines that are both available for the job (on "idle")
    and that the task requires for its completion.
    The machine has to have a last maintenance done.
    """
    return Machine.objects.filter(
        status="idle",
        machine_type=task.required_machine_type
        )

def check_maintenance_need(machine):
    """
    Checks the machine for maintenance.
    Change the status of the machines that need maintenance to "maintenance"
    """
    if machine.needs_maintenance and machine.status == "idle":
        machine.status = "maintenance"
        machine.save()
        return True
    return False


# ActivityLogs
def create_log_event_task(task, log_type, message, user=None):
    """Creates a log for a task."""
    return ActivityLog.objects.create(
            task=task,
            log_type=log_type,
            message=f"[{log_type.upper()}] - {message}",
            user=user
    )