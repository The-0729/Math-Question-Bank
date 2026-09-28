from fastapi import APIRouter,Depends
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Chapter,Difficulty,Exam,Question,QuestionUsage

router=APIRouter(prefix="/api/inspector",tags=["inspector"])

@router.get("")
def database_summary(db:Session=Depends(get_db)):
    active_questions=Question.is_active==True
    by_difficulty=db.execute(
        select(Difficulty.id,Difficulty.name,func.count(Question.id))
        .join(Question,Question.difficulty_id==Difficulty.id)
        .where(active_questions)
        .group_by(Difficulty.id,Difficulty.name,Difficulty.display_order)
        .order_by(Difficulty.display_order)
    ).all()
    by_chapter=db.execute(
        select(Chapter.id,Chapter.code,Chapter.name,func.count(Question.id))
        .outerjoin(Question,(Question.chapter_id==Chapter.id)&active_questions)
        .where(Chapter.is_active==True)
        .group_by(Chapter.id,Chapter.code,Chapter.name,Chapter.display_order)
        .order_by(Chapter.display_order,Chapter.id)
    ).all()
    question_count=db.scalar(select(func.count()).select_from(Question).where(active_questions)) or 0
    used_question_count=db.scalar(
        select(func.count(func.distinct(QuestionUsage.question_id)))
        .join(Question,Question.id==QuestionUsage.question_id)
        .where(active_questions)
    ) or 0
    return {
        "questions":question_count,
        "priority_questions":db.scalar(select(func.count()).select_from(Question).where(active_questions,Question.is_priority==True)) or 0,
        "chapters":db.scalar(select(func.count()).select_from(Chapter).where(Chapter.is_active==True)) or 0,
        "exams":db.scalar(select(func.count()).select_from(Exam)) or 0,
        "used_questions":used_question_count,
        "unused_questions":max(0,question_count-used_question_count),
        "questions_by_difficulty":[{"id":id,"name":{1:"Dễ",2:"Trung bình",3:"Khó"}.get(id,name),"count":count} for id,name,count in by_difficulty],
        "questions_by_chapter":[{"id":id,"code":code,"name":name,"count":count} for id,code,name,count in by_chapter],
    }