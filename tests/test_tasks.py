import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

from cnc_api.workshop.models import Order, Machine, Task, ActivityLog

@pytest.mark.django_db
def test_start_task():
    """
    Creates a task as admin.
    Assigns a machine to the task.
    Creates a log for the started task.
    """
    # Create a user and it's group
    admin = User.objects.create_user(username="admin1", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)

    # Create a machine
    machine1 = Machine.objects.create(
            name="Machine 1 Test",
            machine_type="lathe",
            status="idle",
            location="Zone A1"
    )

    # Create an order
    order1 = Order.objects.create(name="Order 1 Test")
    # Create a task without an assigned machine
    task = Task.objects.create(
            order=order1,
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

    # Check if it exists on the DB
    task.refresh_from_db()
    machine1.refresh_from_db()
    log_exists = ActivityLog.objects.filter(
            task=task,
            log_type="info"
            ).exists()

    assert response.status_code == 200
    assert task.machine == machine1
    assert task.status == "in_progress"
    assert machine1.status == "running"
    assert log_exists


@pytest.mark.django_db
def test_complete_task_and_start_same_machine():
    """"""
    # Create a user and it's group
    admin = User.objects.create_user(username="admin1", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)

    # Create a machine
    machine2 = Machine.objects.create(
            name="Machine 2 Test",
            machine_type="mill",
            status="idle",
            location="Zone A2"
    )

    # Create an order
    order2 = Order.objects.create(name="Order 2 Test")
    # Create two different tasks:
    # task1 has an assigned machine and it's "in_process"
    task1 = Task.objects.create(
            order=order2,
            queue_number=1,
            required_machine_type="mill",
            status="in_progress",
            machine=machine2
    )
    # task2 is a task without an assigned machine, next in queue from task1
    task2 = Task.objects.create(
            order=order2,
            queue_number=2,
            required_machine_type="mill",
            status="pending"
    )

    # Force the authentication without tokens, pass or session
    client = APIClient()
    client.force_authenticate(user=admin)

    # POST the task
    # In this moment a task is assigned
    response = client.post(f"/api/tasks/{task1.task_id}/complete/")

    # Check if it exists on the DB
    task1.refresh_from_db()
    task2.refresh_from_db()
    machine2.refresh_from_db()

    # Check the tasks and the machine
    assert response.status_code == 200
    assert task1.status == "completed"
    assert machine2.status == "running"
    assert task2.status == "in_progress"
    assert task2.machine is not None

    # Check the creation of new logs for task1 completion and task2 start
    assert ActivityLog.objects.filter(
            task=task1,
            log_type="info"
            ).exists()
    assert ActivityLog.objects.filter(
            task=task2,
            log_type="info"
            ).exists()
