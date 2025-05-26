"""
Create the endpoints logic for the classes.
Each class responds to each resource.
ModelViewSet simplifies the API creating CRUD for each model.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order, Machine, Task, ActivityLog
from .permissions import IsAdminOrReadOnly
from .serializers import OrderSerializer, MachineSerializer, TaskSerializer, ActivityLogSerializer
from .services import start_task_with_auto_machine_assignation as start_auto
from .services import create_log_event_task

# Create your views here.
class OrderViewSet(viewsets.ModelViewSet):
    # Give the permissions set in permissions.py
    permission_classes = [IsAdminOrReadOnly]
    
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "date_completion"]

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """
        Start an order.
        Task must have machines assigned.
        Only "pending" tasks can be start ed.
        Then activate the first task.
        """
        order = self.get_object()

        if order.status == "in_progress":
            return Response(
                    {"detail": "Order is already in progress"},
                    status=status.HTTP_400_BAD_REQUEST
            )
        if order.status in ["cancelled", "completed"]:
            return Response(
                    {"detail": "Cannot start a completed or cancelled order."},
                    status=status.HTTP_400_BAD_REQUEST
            )

        # Get the first task on the queue
        first_task = order.tasks.order_by("queue_number").first()
        
        if first_task:
            try:
                # Start the task and log it
                task = start_auto(first_task)
                create_log_event_task(
                        task=task,
                        log_type="info",
                        message=f"{timezone.now()} - '{task.operation}' started - Machine {task.machine.name}",
                        user=request.user if request.user.is_authenticated else None
                )

                # Change the status and save the updated order
                order.status = "in_progress"
                order.date_start = timezone.now()
                order.save()
                
                return Response(
                        {"detail": f"Task {task.task_id} started (machine: '{task.machine.name}')"},
                        status=status.HTTP_200_OK
                )
            except ValidationError as e:
                return Response(
                        {"detail": str(e.detail)},
                        status=status.HTTP_400_BAD_REQUEST
                )


class MachineViewSet(viewsets.ModelViewSet):
    # Give the permissions set in permissions.py
    permission_classes = [IsAdminOrReadOnly]

    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "machine_type"]

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Change the status of a machine."""
        machine = self.get_object()
        new_status = request.data.get("status")

        valid_status = [choice[0] for choice in machine._meta.get_field("status").choices]
        if new_status not in valid_status:
            return Response(
                    {"detail": f"Invalid status. Status can be: {valid_status}"},
                    status=status.HTTP_400_BAD_REQUEST
            )
        
        machine.status = new_status
        machine.save()
        return Response(
                {"details": f"Machine {machine.name} status changed to '{new_status}'"},
                status=status.HTTP_200_OK
        )


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "order", "machine"]

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """
        Starts a task.
        If no machine is assigned, tries to assign one.
        Machines have to be on "idle" and of the correct type.
        Update the status from task, machine and order.
        """
        task = self.get_object()
        try:
            task = start_auto(task)
            # Log the start
            create_log_event_task(
                    task,
                    log_type="info",
                    message=f"{timezone.now()} - '{task.operation}' started - Machine {task.machine.name}",
                    user=request.user if request.user.is_authenticated else None
            )

            return Response(
                    {'detail': f"Task {task.task_id} started (machine: '{task.machine.name})'"},
                    status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                    {"detail": str(e.detail)},
                    status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Completes a task.
        Tasks that are not "in_progress" cannot be completed.
        Task status changes.
        Machine changes to "idle" if it was on "running".
        Next task (if any) starts.
        """
        task = self.get_object()

        if task.status != "in_progress":
            return Response(
                    {"detail": "Cannot complete a task that is not 'in_progress'."},
                    status=status.HTTP_400_BAD_REQUEST
            )
        # Change the status and save the updated task
        task.status = "completed"
        task.finish_time = timezone.now()
        task.save()
        # Create the log for the task completion
        create_log_event_task(
                task,
                log_type="info",
                message=f"{timezone.now()} - '{task.operation}' completed",
                user=request.user if request.user.is_authenticated else None
        )
        # Change the status for the used machine
        task.machine.status = "idle"
        task.machine.save()

        # Look for the next task on the order
        next_task = (
            Task.objects
            .filter(order=task.order, queue_number__gt=task.queue_number, status="pending")
            .order_by("queue_number")
            .first()
        )
        # Start the new task
        if next_task and next_task.status == "pending":
            task = start_auto(next_task)
            create_log_event_task(
                    task,
                    log_type="info",
                    message=f"{timezone.now()} - '{task.operation}' started - Machine {task.machine.name}",
                    user=request.user if request.user.is_authenticated else None
            )

            return Response(
                    {"detail": f"Task {next_task.task_id} completed."},
                    status=status.HTTP_200_OK
            )
        elif not next_task:
            # Complete the Order if there are no more tasks
            task.order.date_completion = timezone.now()
            task.order.status = "completed"
            task.order.save()
            
            return Response(
                    {"detail": "There are no following tasks. Order completed."},
                    status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                    {"detail": "Tasks must be pending in order to be started."},
                    status=status.HTTP_400_BAD_REQUEST
            )


class ActivityLogViewSet(viewsets.ModelViewSet):
    # Give the permissions set in permissions.py
    permission_classes = [IsAdminOrReadOnly]

    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["log_type", "task"]
