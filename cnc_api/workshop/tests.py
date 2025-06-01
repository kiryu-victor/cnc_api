from django.test import TestCase
import io
import csv
import json

# Create your tests here.
import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from datetime import timedelta
from django.utils import timezone

from cnc_api.workshop.models import Order, Machine, Task, ActivityLog

# TEST ORDER
@pytest.mark.django_db
def test_order_creation_and_retrieval():
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post("/api/orders/", {"name": "Order X"}, format="json")
    assert response.status_code == 201
    order_id = response.data["order_id"]

    get_response = client.get(f"/api/orders/{order_id}/")
    assert get_response.status_code == 200
    assert get_response.data["name"] == "Order X"


# TEST MACHINES
@pytest.mark.django_db
def test_create_machine_as_admin():
    """
    Create an admin and add it to "admin" group.
    Login as that admin.
    Try to create a machine in a post request.
    Assert the status code.
    Assert that the machine has been created successfully.
    """
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(
            "/api/machines/",
            {
                "name": "Machine 1 Test",
                "machine_type": "mill",
                "status": "idle",
                "location": "Zone A"
            },
            format="json"
    )

    assert response.status_code == 201
    assert Machine.objects.count() == 1

@pytest.mark.django_db
def test_create_machine_as_non_admin():
    """
    Create a regular operator.
    Login as said operator.
    Try to create a machine in a post request.
    Assert the status code.
    Assert that the machine has not been created.
    """
    operator = User.objects.create_user(username="op1", password="operator123")
    group = Group.objects.create(name="operator")
    operator.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=operator)

    response = client.post(
            "/api/machines/",
            {
                "name": "Machine 2 Test",
                "machine_type": "lathe",
                "status": "idle",
                "location": "Zone B"
            },
            format="json"
    )

    assert response.status_code == 403
    assert Machine.objects.count() == 0

@pytest.mark.django_db
def test_machine_cannot_be_assigned_to_two_tasks():
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    machine = Machine.objects.create(
        name="Machine Double Assign",
        machine_type="lathe",
        status="idle",
        location="Zone X"
    )
    order = Order.objects.create(name="Order Double Assign")
    task1 = Task.objects.create(
        order=order,
        queue_number=1,
        required_machine_type="lathe",
        status="pending"
    )
    task2 = Task.objects.create(
        order=order,
        queue_number=2,
        required_machine_type="lathe",
        status="pending"
    )

    # Start first task (should succeed)
    response1 = client.put(f"/api/tasks/{task1.task_id}/start/")
    assert response1.status_code == 200

    # Try to start second task (should fail, machine busy)
    response2 = client.put(f"/api/tasks/{task2.task_id}/start/")
    assert response2.status_code == 400
    task2.refresh_from_db()
    assert task2.status == "pending"

# TEST MAINTENANCE
@pytest.mark.django_db
def test_cannot_start_task_on_machine_on_maintenance():
    # Create a user and its group
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    # Ensure the gap for passing maintenance is less that then gap of days
    # from last maintenance to the present
    date = timezone.now().date() - timedelta(days=20)
    # Create a machine under maintenance
    machine = Machine.objects.create(
            name="Machine 2 Test",
            machine_type="lathe",
            status="maintenance",
            location="Zone A1",
            last_maintenance=date,
            maintenance_gap_days=10 
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

    # PUT the task
    # In this moment a machine is assigned to the task
    # But it cannot be done because the machine is under maintenanace
    response = client.put(f"/api/tasks/{task.task_id}/start/")

    assert response.status_code == 400
    assert task.status == "pending"
    assert task.machine is None
    assert machine.status == "maintenance"


# TEST TASKS
@pytest.mark.django_db
def test_start_task():
    """
    Creates a task as admin.
    Assigns a machine to the task.
    Creates a log for the started task.
    """
    # Create a user and it's group
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    # Create a machine
    machine1 = Machine.objects.create(
            name="Machine 4 Test",
            machine_type="lathe",
            status="idle",
            location="Zone A1"
    )

    # Create an order
    order1 = Order.objects.create(name="Order 4 Test")
    # Create a task without an assigned machine
    task = Task.objects.create(
            order=order1,
            queue_number=1,
            required_machine_type="lathe",
            status="pending"
    )

    # PUT the task
    # In this moment a task is assigned
    response = client.put(f"/api/tasks/{task.task_id}/start/")

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
def test_task_cannot_start_if_no_machine_of_type():
    admin = User.objects.create_user(username="admin4", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    order = Order.objects.create(name="Order No Machine")
    task = Task.objects.create(
        order=order,
        queue_number=1,
        required_machine_type="grinder",
        status="pending"
    )

    response = client.put(f"/api/tasks/{task.task_id}/start/")
    assert response.status_code == 400
    task.refresh_from_db()
    assert task.status == "pending"

@pytest.mark.django_db
def test_complete_task_and_start_same_machine():
    """"""
    # Create a user and it's group
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    # Force the authentication without tokens, pass or session
    client = APIClient()
    client.force_authenticate(user=admin)

    # Create a machine
    machine2 = Machine.objects.create(
            name="Machine 5 Test",
            machine_type="mill",
            status="idle",
            location="Zone A2"
    )

    # Create an order
    order2 = Order.objects.create(name="Order 5 Test")
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

    # PUT the task
    # In this moment a task is assigned
    response = client.put(f"/api/tasks/{task1.task_id}/complete/")

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


# TEST ACTIVITYLOG
@pytest.mark.django_db
def test_machine_status_updates_on_task_complete():
    admin = User.objects.create_user(username="admin7", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    machine = Machine.objects.create(
        name="Machine Status",
        machine_type="lathe",
        status="running",
        location="Zone S"
    )
    order = Order.objects.create(name="Order Status")
    task = Task.objects.create(
        order=order,
        queue_number=1,
        required_machine_type="lathe",
        status="in_progress",
        machine=machine
    )

    response = client.put(f"/api/tasks/{task.task_id}/complete/")
    assert response.status_code == 200
    machine.refresh_from_db()
    # Depending on next task assignment
    assert machine.status in ["idle", "running"]

@pytest.mark.django_db
def test_activity_log_created_on_task_complete():
    # Create a user and it's group
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    # Force the authentication without tokens, pass or session
    client = APIClient()
    client.force_authenticate(user=admin)

    machine = Machine.objects.create(
        name="Machine Log",
        machine_type="lathe",
        status="idle",
        location="Zone Z"
    )
    order = Order.objects.create(name="Order Log")
    task = Task.objects.create(
        order=order,
        queue_number=1,
        required_machine_type="lathe",
        status="in_progress",
        machine=machine
    )

    response = client.put(f"/api/tasks/{task.task_id}/complete/")
    assert response.status_code == 200
    assert ActivityLog.objects.filter(task=task, log_type="info").exists()






# INTEGRATION TESTS
@pytest.mark.django_db
def test_list_orders():
    """
    Test listing all orders via the API endpoint.
    """
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    Order.objects.create(name="Order 1")
    Order.objects.create(name="Order 2")
    response = client.get("/api/orders/")

    assert response.status_code == 200
    assert len(response.data) >= 2

@pytest.mark.django_db
def test_retrieve_machine_by_id():
    """
    Test retrieving a machine by its ID via the API endpoint.
    """
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    machine = Machine.objects.create(name="Machine X", machine_type="lathe", status="idle", location="A")
    response = client.get(f"/api/machines/{machine.machine_id}/")

    assert response.status_code == 200
    assert response.data["name"] == "Machine X"

@pytest.mark.django_db
def test_list_tasks():
    """
    Test listing all tasks via the API endpoint.
    """
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    order = Order.objects.create(name="Order for Tasks")
    Task.objects.create(order=order, queue_number=1, required_machine_type="lathe", status="pending")
    Task.objects.create(order=order, queue_number=2, required_machine_type="lathe", status="pending")
    response = client.get("/api/tasks/")

    assert response.status_code == 200
    assert len(response.data) >= 2

@pytest.mark.django_db
def test_retrieve_activitylog_by_id():
    """
    Test retrieving an activity log by its ID via the API endpoint.
    """
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)

    order = Order.objects.create(name="Order for Log")
    task = Task.objects.create(order=order, queue_number=1, required_machine_type="lathe", status="pending")
    log = ActivityLog.objects.create(task=task, log_type="info", message="Test log")
    response = client.get(f"/api/activitylogs/{log.log_id}/")
    
    assert response.status_code == 200
    assert response.data["message"] == "Test log"

@pytest.mark.django_db
def test_export_activitylogs_json():
    """
    Test exporting activity logs as JSON via the API endpoint.
    """
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)
    
    order = Order.objects.create(name="Order for Export")
    task = Task.objects.create(order=order, queue_number=1, required_machine_type="lathe", status="pending")
    ActivityLog.objects.create(task=task, log_type="info", message="Export log")
    response = client.get("/api/activitylogs/export/json/")
    
    assert response.status_code == 200
    assert response["Content-Disposition"].startswith("attachment;")
    data = json.loads(response.content)
    assert isinstance(data, list)

@pytest.mark.django_db
def test_export_activitylogs_csv():
    """
    Test exporting activity logs as CSV via the API endpoint.
    """
    admin = User.objects.create_user(username="admin", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)
    client = APIClient()
    client.force_authenticate(user=admin)
    
    order = Order.objects.create(name="Order for Export CSV")
    task = Task.objects.create(order=order, queue_number=1, required_machine_type="lathe", status="pending")
    ActivityLog.objects.create(task=task, log_type="info", message="Export log CSV")
    response = client.get("/api/activitylogs/export/csv/")
    
    assert response.status_code == 200
    assert response["Content-Disposition"].startswith("attachment;")
    
    # Check CSV content
    content = response.content.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert rows[0] == ['log_id', 'log_type', 'message', 'time', 'task_id', 'user_id', 'username']
    assert any("Export log CSV" in row for row in rows)