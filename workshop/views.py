"""
Create the endpoints logic for the classes.
Each class responds to each resource.
ModelViewSet simplifies the API creating CRUD for each model.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order, Machine, Task, ActivityLog
from .permissions import IsAdminOrReadOnly
from .serializers import OrderSerializer, MachineSerializer, TaskSerializer, ActivityLogSerializer

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
        Then activate the first task.
        Only "pending" tasks can be started.
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
        # Change the status and save the updated order
        order.status = "in_progress"
        order.save()

        # Get the first task on the queue
        first_task = order.tasks.order_by("queue_number").first()
        # Start it
        if first_task and first_task.status == "pending":
            first_task.status = "in_progress"
            first_task.start_time  = timezone.now()
            first_task.save()
            message = f"Order started. Task '{first_task.operation}' is in progress."
        else:
            message = "Order started. No tasks on queue activated."

        return Response({"detail": message})

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
        print(valid_status)
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
    def complete(self, request, pk=None):
        """
        Completes a task.
        Tasks that are not "in_progress" cannot be completed.
        """
        task = self.get_object()
        if task.status != "in_progress":
            return Response(
                    {'detail': 'Cannot complete a task that is not "in_progress".'},
                    status=status.HTTP_400_BAD_REQUEST
            )
        # Change the status and save the updated task
        task.status = "completed"
        task.save()

        # Look for the next task on the order and start it
        next_task = (
            Task.objects
            .filter(
                    order=task.order, queue_number__gt=task.queue_number, status="pending")
            .order_by("queue_number")
            .first()
        )
        print(next_task)

        message = f"Task {task.task_id} completed."

        if next_task and next_task.status == "pending":
            next_task.status = "in_progress"
            next_task.start_time = timezone.now()
            next_task.save()
            message += f" Task {next_task.task_id} started."

        return Response(
                {"detail": message},
                status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=["post"])
    def assign_machine(self, request, pk=None):
        """
        Assign a machine to a certain task.
        Only "pending" tasks can be assigned to a machine.
        """
        task = self.get_object()

        if task.status != "pending":
            return Response(
                    {"detail": "Cannot assign a machine to a task that is no pending."},
                    status=status.HTTP_400_BAD_REQUEST
            )

        machine_id = request.data.get("machine_id")

        try:
            machine = Machine.objects.get(id=machine_id)
        except Machine.DoesNotExist:
            return Response(
                    {"detail": "That machine does not exist."},
                    status=status.HTTP_404_NOT_FOUND
            )
        # Set the assigned machine and save the updated task
        task.machine = machine
        task.save()
        return Response(
                {"detail": f"Machine {machine.name} assigned to Task {task.id}"},
                status=status.HTTP_200_OK
        )

class ActivityLogViewSet(viewsets.ModelViewSet):
    # Give the permissions set in permissions.py
    permission_classes = [IsAdminOrReadOnly]

    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["log_type", "task"]
