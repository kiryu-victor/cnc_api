from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Machine


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
        if not available_machines.exists():
            raise ValidationError("No machines of the required type available.")
        
        # Assign a machine, change it status, save it
        machine = available_machines.first()
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
    """
    return Machine.objects.filter(
        status="idle",
        machine_type=task.required_machine_type
    )
