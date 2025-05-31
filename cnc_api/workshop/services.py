from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Machine, ActivityLog

# Machine
def start_task_with_auto_machine_assignation(task):
    """
    Starts a task.
    Checks it is "pending".
    Assigns an "idle" machine of the required type.
    Updates the task and machine status.
    Updates the order status if needed if it's the first tasks.
    """
    if task.status != "pending":
        raise ValidationError('Only tasks with "pending" status can be started.')
    # Look into the machines with in case there is one with "idle" status that needs maintenance
    check_need_maintenance_all_machines()

    # If there is no machine assigned to the task yet
    if not task.machine:
        # Get the machines that can take the task
        available_machines = Machine.objects.filter(
                status="idle",
                machine_type=task.required_machine_type
        )
        if not available_machines:
            raise ValidationError("No machines of the required type available.")
        # Set the first machine on the list that fulfill the requirements
        machine = available_machines[0]
        task.machine = machine
        # Set the new status on the machine and save it
        machine.status = "running"
        machine.save()
        # Do the same with the task and set its start_time
        task.status = "in_progress"
        task.start_time = timezone.now()
        task.save()
    return task


def check_need_maintenance_all_machines():
    """
    Changes the status of those machines that have "idle" status
    when they should be on "maintenance" instead.
    """
    # Filter "idle" machines alone
    machines = Machine.objects.filter(
        status="idle"
    )
    # From those, get the ones that need maintenance and save their new status
    for m in machines:
        if m.needs_maintenance:
            m.status = "maintenance"
            m.save()
            create_log_event_task(
                    task=None,
                    log_type="warning",
                    message=f"{m.name} is now under MAINTENANCE"
            )


# ActivityLogs
def create_log_event_task(task, log_type, message, user=None):
    """Creates a log for a task."""
    return ActivityLog.objects.create(
            task=task,
            log_type=log_type,
            message=f"[{log_type.upper()}] - {message}",
            user=user
    )