from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import OrderViewSet, MachineViewSet, TaskViewSet, ActivityLogViewSet

# Create a DefaultRouter instance to automatically generate URL patterns for the viewsets
router = DefaultRouter()
# Register the OrderViewSet with the 'orders' endpoint
router.register(r"orders", OrderViewSet)
# Do similar with the other ViewSets
router.register(r"machines", MachineViewSet)
router.register(r"tasks", TaskViewSet)
router.register(r"activitylogs", ActivityLogViewSet)

# Define the URL patterns for this app
urlpatterns = [
    # Include all automatically generated routes from the router
    path("", include(router.urls)),
]