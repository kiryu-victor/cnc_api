import os
import django
import matplotlib.pyplot as plt
import pandas as pd

# Configure the environment to use ORM outside from the server
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cnc_api.settings")
django.setup()
# It had to be configured before the import
from workshop.models import ActivityLog


# Filter logs to get only the "maintenance" ones
logs = ActivityLog.objects.filter(log_type="warning").select_related("task")

data = []
for log in logs:
    machine = log.task.machine
    if machine:
        data.append(machine.name)

df = pd.DataFrame(data, columns=["machine"])
count_df = df["machine"].value_counts()

plt.figure(figsize=(10,6))
count_df.plot(kind="bar", color="darkred")
plt.title("Maintenance count per machine")
plt.ylabel("Maintenances")
plt.xlabel("Machine")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("reports/maintenance_by_machine.png")