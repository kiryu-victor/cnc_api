## What is this?

**This is a WIP project** consisting of an API REST simulating the task and order management in a CNC workshop.

It includes machine control, an automatic queue of tasks, JWT authentication and role control systems.

> [!NOTE]
> For the moment, the data in this project is simplified and non-realistic to prioritize learning and clarity.


## How does it work?

- An **order** is created in the workshop.
- Each order contains **tasks** that must be completed in a specific order.
  - A task must be assigned to a **machine** so it can start.
  - Tasks have a status to track how is the process going, a start time and an expected time of completion, along with their position on the queue.
- **Machines** are the resources that execute tasks.
  - They have a name, type, status, a location and a description.
  - That are some restrictions that apply to machines and their status (for example, a machine in "maintenance" should take a tasks after the maintenance is done).
- Some issues can happen during the execution of the order. **Logs** can track what has happened in detail.


## How is it made?
#### Tech used:
Python, venv, PostgreSQL, Django, Django REST Framework (DRF), drf-yasg (documentation), pytest, SimpleJWT (auth)

#### TLDR:
1. Order arrives.
2. Idle machines are needed.
3. Every order goes through stages (tasks).
4. The order starts.
5. The first task starts immediately if the machine is functional and waiting for a task.
6. A task completes. A new task starts.
7. Issues trigger log entries.
8. All tasks are done. The order is "completed".


## But... why?

I'm making this project because I want to learn REST API. As I want to keep learning Python I've used this language for this project. With this I'm learning:

- REST API
- Python
- PostgreSQL
- Django
- DRF
- Docker

Stretch goals will come after I focus in polishing "unfinished" core implementations that you can find on the **To-do list**.

## To-do list
- [x] **Machine availability logic**
  - [x] Auto assign idle machines
  - [x] Auto free running machines when a task is over
- [x] **Preventive maintenance** rules
  - [ ] Based on usage
  - [x] Based on time
  - [x] Pre-task maintenance checks
- [x] **Status restrictions**
  - [x] Machines in "maintenance" cannot start a task.
- [ ] Create a **report export**
  - [x] JSON and CSV format (no PDF)
    - [x] JSON format
    - [x] CSV format
  - [ ] Metrics: usage, time, logs...
- [ ] **Tracking**
  - [ ] Users, materials, time, machines used...
  - [ ] Graphics? (matplotlib and such)
- [ ] **Dockerize** the project
  - [ ] Both the app and PostgreSQL DB
- [ ] ...

#### Stretch goals
- [ ] Frontend for operators and other personnel.
- [ ] WebSocket notifications
> [!NOTE]
> My other project, [task-generator](https://github.com/kiryu-victor/task_generator), already has WebSocket implemented. For the sake of optimising practice time I am leaving this out of the scope, or for a later stage.
- [ ] ...