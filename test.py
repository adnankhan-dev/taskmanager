from datetime import date
from app.database import SessionLocal
from app.services.task_service import create_task
from app.services.milestone_service import add_milestone, update_milestone_status

db = SessionLocal()

task = create_task(
    db,
    title="Prepare BASR Minutes",
    task_type="Directorate",
    final_deadline=date(2026, 2, 10)
)

m1 = add_milestone(db, task, "Draft", date(2026, 2, 5))
m2 = add_milestone(db, task, "Review", date(2026, 2, 8))

update_milestone_status(db, m1, "Completed")
update_milestone_status(db, m2, "Completed")

assert task.status == "Completed"
print("Task status:", task.status)
