from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {
        "app": "Task Management System v2",
        "status": "running",
        "docs": "/docs"
    }
