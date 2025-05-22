"""
Take a model and convert it to JSON format.
"""

from rest_framework import serializers
from .models import Order, Machine, Task, ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = "__all__"

class TaskSerializer(serializers.ModelSerializer):
    logs = ActivityLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = "__all__"

class MachineSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = Machine
        fields = "__all__"