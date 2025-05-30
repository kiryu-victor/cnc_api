"""
Creates a .png report with the average of the tasks, grouped by machine,
that have been created.
It can be filtered by period using the form:
python -m reports.task_average_time --from YYYY-MM-DD --to YYYY-MM-DD
"""

import argparse
import django
import matplotlib.pyplot as plt
import os
import pandas as pd

from datetime import datetime

# Configure the environment to use ORM outside from the server
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cnc_api.settings")
django.setup()
# It had to be configured before the import
from workshop.models import Task


# Parser with description
parser = argparse.ArgumentParser(description="Get the average task duration graph.")
# Include the arguments
parser.add_argument(
        "--from",
        dest="from_date",
        help="Start date in YYYY-MM-DD format.",
        required=False)
parser.add_argument(
        "--to",
        dest="to_date",
        help="End date in YYYY-MM-DD format.",
        required=False)
args = parser.parse_args()

# Get the start and end date so they can be passed as filter later
start_date = datetime.strptime(args.from_date, "%Y-%m-%d") if args.from_date else None
end_date = datetime.strptime(args.to_date, "%Y-%m-%d") if args.to_date else None


# Get the completed tasks
# Added an start time filter to avoid failures
tasks = Task.objects.filter(
        status="completed",
        start_time__isnull=False
)
# Filter further in the case of date range is indicated
if start_date:
    tasks = tasks.filter(start_time__date__gte=start_date.date())
if end_date:
    tasks = tasks.filter(finish_time__date__lte=start_date.date())

# List of dictionaries with the data
data = []
for task in tasks:
    if not task.finish_time:
        continue
    # Duration in seconds
    duration = (task.finish_time - task.start_time).total_seconds()
    data.append({
            "machine": task.machine.name,
            "duration_seconds": duration
    })

# Create DataFrame
df = pd.DataFrame(data)

# Group by machine and get average
avg_df = df.groupby("machine").mean(numeric_only=True).sort_values("duration_seconds")

# Create a new figure with horizontal bars
plt.figure(figsize=(10,6))
plt.barh(avg_df.index, avg_df["duration_seconds"], color="steelblue")
plt.xlabel("Average time (seconds)")
plt.title("Average task time per machine")
plt.tight_layout()

# Save the graphic as PNG
plt.savefig("reports/average_task_duration.png")