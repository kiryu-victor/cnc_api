import os
import django
import matplotlib.pyplot as plt
import pandas as pd

# Configure the environment to use ORM outside from the server
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cnc_api.settings")
django.setup()
# It had to be configured before the import
from cnc_api.workshop.models import ActivityLog


# Filter logs to get only the "maintenance" ones
logs = ActivityLog.objects.filter(log_type="warning").select_related("task")

data = []
for log in logs:
    # Get the machine from the log message as a substring
    # Used to avoid issues with maintenance when no task is assigned
    starting_position = log.message.find("- ") + 2
    ending_position = log.message.find(" is")
    machine = log.message[starting_position:ending_position]
    data.append(machine)

if not data:
    print("There are no maintenance logs to be shown.")
else:
    df = pd.DataFrame(data, columns=["machine"])
    count_df = df["machine"].value_counts().sort_index()

    plt.figure(figsize=(10,6))
    count_df.plot(kind="bar", color="darkred")
    plt.title("Maintenance count per machine")
    plt.ylabel("Maintenances")
    plt.xlabel("Machine")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig("cnc_api/reports/maintenance_by_machine.png")