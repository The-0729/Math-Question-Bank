from fastapi import APIRouter,Depends
from sqlalchemy import case,func,select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Chapter,Difficulty,Exam,Question,QuestionOption,QuestionUsage

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
    answer_rows=db.execute(
        select(Question.answers_confirmed,func.sum(case((func.trim(QuestionOption.content)!="",1),else_=0)))
        .select_from(Question)
        .outerjoin(QuestionOption,QuestionOption.question_id==Question.id)
        .where(active_questions)
        .group_by(Question.id,Question.answers_confirmed)
    ).all()
    answer_status_counts={"confirmed":0,"unconfirmed":0,"missing":0}
    for confirmed,answer_count in answer_rows:
        if not answer_count:
            answer_status_counts["missing"]+=1
        elif confirmed:
            answer_status_counts["confirmed"]+=1
        else:
            answer_status_counts["unconfirmed"]+=1
    return {
        "questions":question_count,
        "priority_questions":db.scalar(select(func.count()).select_from(Question).where(active_questions,Question.is_priority==True)) or 0,
        "chapters":db.scalar(select(func.count()).select_from(Chapter).where(Chapter.is_active==True)) or 0,
        "exams":db.scalar(select(func.count()).select_from(Exam)) or 0,
        "used_questions":used_question_count,
        "unused_questions":max(0,question_count-used_question_count),
        "confirmed_answers":answer_status_counts["confirmed"],
        "unconfirmed_answers":answer_status_counts["unconfirmed"],
        "questions_without_answers":answer_status_counts["missing"],
        "questions_by_answer_status":[
            {"id":"confirmed","name":"Đã xác nhận","count":answer_status_counts["confirmed"]},
            {"id":"unconfirmed","name":"Chưa xác nhận","count":answer_status_counts["unconfirmed"]},
            {"id":"missing","name":"Chưa có đáp án","count":answer_status_counts["missing"]},
        ],
        "questions_by_difficulty":[{"id":id,"name":{1:"Dễ",2:"Trung bình",3:"Khó"}.get(id,name),"count":count} for id,name,count in by_difficulty],
        "questions_by_chapter":[{"id":id,"code":code,"name":name,"count":count} for id,code,name,count in by_chapter],
    }