from io import BytesIO
import os
from datetime import datetime, date
from sqlalchemy.orm import Session
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

from app.models.task import Task
from app.models.quick_task import QuickTask


def _apply_filters(query, from_date, to_date, status):
    if from_date:
        query = query.filter(Task.final_deadline >= from_date)
    if to_date:
        query = query.filter(Task.final_deadline <= to_date)
    if status:
        query = query.filter(Task.status == status)
    return query


# -------- EXCEL REPORT --------
def generate_tasks_excel(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    status: str | None,
    columns: list[str] | None = None
) -> BytesIO:

    wb = Workbook()
    ws = wb.active
    ws.title = "Tasks Report"

    column_labels = {
        "id": "Task ID",
        "title": "Title",
        "status": "Status",
        "priority": "Priority",
        "assigned_to": "Assigned To",
        "deadline": "Final Deadline",
        "folder": "Folder",
        "milestone": "Milestone",
        "milestone_status": "Milestone Status",
        "milestone_deadline": "Milestone Deadline",
    }
    if not columns:
        columns = list(column_labels.keys())

    ws.append([column_labels[c] for c in columns])

    query = db.query(Task).filter(Task.archived == False)
    query = _apply_filters(query, from_date, to_date, status)

    tasks = query.all()

    quick_q = db.query(QuickTask)
    if status and status != "Completed":
        quick_tasks = []
    else:
        if from_date:
            quick_q = quick_q.filter(QuickTask.completed_on >= from_date)
        if to_date:
            quick_q = quick_q.filter(QuickTask.completed_on <= to_date)
        quick_tasks = quick_q.all()

    milestone_columns = {"milestone", "milestone_status", "milestone_deadline"}
    include_milestones = any(c in milestone_columns for c in columns)

    def task_row(task, blank_milestones: bool):
        values = {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "assigned_to": task.assigned_to.username if task.assigned_to else "-",
            "deadline": task.final_deadline,
            "folder": task.folder_link or "-",
            "milestone": "" if blank_milestones else "-",
            "milestone_status": "" if blank_milestones else "-",
            "milestone_deadline": "" if blank_milestones else "-",
        }
        return [values[c] for c in columns]

    def milestone_row(m):
        values = {
            "id": "",
            "title": "",
            "status": "",
            "priority": "",
            "assigned_to": "",
            "deadline": "",
            "folder": "",
            "milestone": m.title,
            "milestone_status": m.status,
            "milestone_deadline": m.deadline,
        }
        return [values[c] for c in columns]

    for task in tasks:
        if task.milestones and include_milestones:
            ws.append(task_row(task, blank_milestones=True))
            for m in task.milestones:
                ws.append(milestone_row(m))
        else:
            ws.append(task_row(task, blank_milestones=False))

    for qt in quick_tasks:
        values = {
            "id": f"Q-{qt.id}",
            "title": qt.title,
            "status": "Completed",
            "priority": "Normal",
            "assigned_to": qt.created_by.username if qt.created_by else "-",
            "deadline": qt.completed_on,
            "folder": "-",
            "milestone": "-",
            "milestone_status": "-",
            "milestone_deadline": "-",
        }
        ws.append([values[c] for c in columns])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


# -------- PDF REPORT --------
def generate_tasks_pdf(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    status: str | None,
    columns: list[str] | None = None
) -> BytesIO:

    buffer = BytesIO()
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=36
    )

    elements = []

    logo_path = os.path.join("app", "static", "img", "uw-logo.png")
    header_cells = []
    if os.path.exists(logo_path):
        header_cells.append(Image(logo_path, width=40, height=40))
    else:
        header_cells.append(Paragraph("UW", styles["Heading2"]))
    header_cells.append(
        Paragraph(
            "Directorate of Academics, Advanced Studies and Research<br/>"
            "Task & Milestone Report",
            styles["Heading2"]
        )
    )
    header = Table([header_cells], colWidths=[50, 460])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(header)
    elements.append(
        Paragraph(
            f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M')}",
            styles['Normal']
        )
    )
    elements.append(
        Paragraph(
            f"Filters: From {from_date or '-'} | To {to_date or '-'} | Status {status or 'All'}",
            styles['Normal']
        )
    )
    elements.append(Spacer(1, 12))

    query = db.query(Task).filter(Task.archived == False)
    query = _apply_filters(query, from_date, to_date, status)

    tasks = query.all()

    quick_q = db.query(QuickTask)
    if status and status != "Completed":
        quick_tasks = []
    else:
        if from_date:
            quick_q = quick_q.filter(QuickTask.completed_on >= from_date)
        if to_date:
            quick_q = quick_q.filter(QuickTask.completed_on <= to_date)
        quick_tasks = quick_q.all()

    column_labels = {
        "id": "ID",
        "title": "Task",
        "status": "Status",
        "priority": "Priority",
        "assigned_to": "Assigned To",
        "deadline": "Deadline",
        "folder": "Folder",
        "milestone": "Milestone",
        "milestone_status": "MS Status",
        "milestone_deadline": "MS Deadline",
    }
    if not columns:
        columns = list(column_labels.keys())

    data = [[column_labels[c] for c in columns]]

    body_style = styles['BodyText']

    milestone_columns = {"milestone", "milestone_status", "milestone_deadline"}
    include_milestones = any(c in milestone_columns for c in columns)

    def task_row(task, blank_milestones: bool):
        values = {
            "id": str(task.id),
            "title": Paragraph(task.title, body_style),
            "status": task.status,
            "priority": task.priority,
            "assigned_to": task.assigned_to.username if task.assigned_to else "-",
            "deadline": task.final_deadline.strftime("%Y-%m-%d") if task.final_deadline else "-",
            "folder": task.folder_link or "-",
            "milestone": "" if blank_milestones else "-",
            "milestone_status": "" if blank_milestones else "-",
            "milestone_deadline": "" if blank_milestones else "-",
        }
        return [values[c] for c in columns]

    def milestone_row(m):
        values = {
            "id": "",
            "title": "",
            "status": "",
            "priority": "",
            "assigned_to": "",
            "deadline": "",
            "folder": "",
            "milestone": Paragraph(m.title, body_style),
            "milestone_status": m.status,
            "milestone_deadline": m.deadline.strftime("%Y-%m-%d") if m.deadline else "-",
        }
        return [values[c] for c in columns]

    if tasks:
        for task in tasks:
            if task.milestones and include_milestones:
                data.append(task_row(task, blank_milestones=True))
                for m in task.milestones:
                    data.append(milestone_row(m))
            else:
                data.append(task_row(task, blank_milestones=False))

    if quick_tasks:
        for qt in quick_tasks:
            values = {
                "id": f"Q-{qt.id}",
                "title": Paragraph(qt.title, body_style),
                "status": "Completed",
                "priority": "Normal",
                "assigned_to": qt.created_by.username if qt.created_by else "-",
                "deadline": qt.completed_on.strftime("%Y-%m-%d") if qt.completed_on else "-",
                "folder": "-",
                "milestone": "-",
                "milestone_status": "-",
                "milestone_deadline": "-",
            }
            data.append([values[c] for c in columns])
    if not tasks and not quick_tasks:
        data.append(['-', 'No tasks found', '-', '-', '-', '-', '-', '-', '-'])

    col_widths_map = {
        "id": 24,
        "title": 90,
        "status": 55,
        "priority": 45,
        "assigned_to": 60,
        "deadline": 55,
        "folder": 90,
        "milestone": 90,
        "milestone_status": 50,
        "milestone_deadline": 54,
    }
    col_widths = [col_widths_map[c] for c in columns]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2d3d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return buffer

def get_filtered_tasks(db: Session, filters: dict):
    query = db.query(Task).filter(Task.archived == False)

    if filters.get("status"):
        query = query.filter(Task.status == filters["status"])

    if filters.get("priority"):
        query = query.filter(Task.priority == filters["priority"])

    if filters.get("type_id"):
        query = query.filter(Task.type_id == filters["type_id"])

    if filters.get("assigned_to_id"):
        query = query.filter(Task.assigned_to_id == filters["assigned_to_id"])

    if filters.get("from_date"):
        query = query.filter(Task.final_deadline >= filters["from_date"])

    if filters.get("to_date"):
        query = query.filter(Task.final_deadline <= filters["to_date"])

    return query.order_by(Task.final_deadline.asc()).all()
