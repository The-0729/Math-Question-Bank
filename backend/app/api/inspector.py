from fastapi import APIRouter,Depends
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Chapter,Exam,Question,QuestionOption,QuestionUsage

router=APIRouter(prefix="/api/inspector",tags=["inspector"])

@router.get("")
def database_summary(db:Session=Depends(get_db)):
    return {
        "questions":db.scalar(select(func.count()).select_from(Question).where(Question.is_active==True)) or 0,
        "options":db.scalar(select(func.count()).select_from(QuestionOption)) or 0,
        "chapters":db.scalar(select(func.count()).select_from(Chapter).where(Chapter.is_active==True)) or 0,
        "exams":db.scalar(select(func.count()).select_from(Exam)) or 0,
        "usage_records":db.scalar(select(func.count()).select_from(QuestionUsage)) or 0,
    }