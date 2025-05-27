import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

from workshop.models import Order, Machine, Task

@pytest.mark.django_db
def test_cannot_start_task_on_machine_on_maintenance():
    # Create a user and it's group
    admin = User.objects.create_user(username="admin1", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)

    # Make sure 
    date = timezone.now().date() - timedelta(days=20)
    # Create a machine
    machine = Machine.objects.create(
            name="Machine 1 Test",
            machine_type="lathe",
            status="idle",
            location="Zone A1",
            last_maintenance=date,
            maintenance_gap_days=30
    )

    # Create an order
    order = Order.objects.create(name="Order Maintenance Test")
    # Create a task without an assigned machine
    task = Task.objects.create(
            order=order,
            queue_number=1,
            required_machine_type="lathe",
            status="pending"
    )

    # Force the authentication without tokens, pass or session
    client = APIClient()
    client.force_authenticate(user=admin)

    # POST the task
    # In this moment a task is assigned
    response = client.post(f"/api/tasks/{task.task_id}/start/")

    assert response.status_code == 400
    assert task.status == "pending"
    assert task.machine is None
    assert machine.status == "idle"