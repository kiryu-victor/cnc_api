import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Group
from workshop.models import Machine

@pytest.mark.django_db
def test_create_machine_as_admin():
    """
    Create an admin and add it to "admin" group.
    Login as that admin.
    Try to create a machine in a post request.
    Assert the status code.
    Assert that the machine has been created successfully.
    """
    admin = User.objects.create_user(username="admin1", password="admin123")
    group = Group.objects.create(name="admin")
    admin.groups.add(group)

    client = APIClient()
    # Force the authentication without tokens, pass or session
    client.force_authenticate(user=admin)
    # The client should do with the session credentials, but it expects an auth
    # client.login(username="admin1", password="admin123")

    response = client.post(
            "/api/machines/",
            {
                "name": "GMM G200",
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
    user = User.objects.create_user(username="ope1", password="operator123")
    group = Group.objects.create(name="operator")
    user.groups.add(group)

    client = APIClient()
    # Force the authentication without tokens, pass or session
    client.force_authenticate(user=user)

    response = client.post(
            "/api/machines/",
            {
                "name": "GLM G201",
                "machine_type": "lathe",
                "status": "idle",
                "location": "Zone B"
            },
            format="json"
    )

    assert response.status_code == 403
    assert Machine.objects.count() == 0