# Generated by Django 5.2.1 on 2025-05-29 17:30

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workshop', '0012_alter_machine_last_maintenance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='last_maintenance',
            field=models.DateField(default=datetime.datetime(2025, 5, 29, 17, 30, 58, 504125, tzinfo=datetime.timezone.utc)),
        ),
    ]
