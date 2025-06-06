# Generated by Django 5.2.1 on 2025-05-23 19:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workshop', '0005_alter_task_required_machine_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='machine',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='workshop.machine'),
        ),
        migrations.AlterField(
            model_name='task',
            name='required_machine_type',
            field=models.CharField(choices=[('lathe', 'Lathe'), ('mill', 'Mill'), ('grinder', 'Grinder'), ('other', 'Other')], default='lathe', max_length=20),
        ),
    ]
