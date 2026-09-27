import random
from datetime import datetime
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from ..db.models import Question,QuestionOption,Exam,ExamQuestion,ExamQuestionOption,QuestionUsage

LETTERS=["A","B","C","D"]

def preflight(db:Session,chapter_ids,quotas):
    report=[]; ok=True
    for difficulty_id,required in quotas.items():
        stmt=select(func.count(Question.id)).where(Question.is_active==True,Question.difficulty_id==difficulty_id)
        if chapter_ids: stmt=stmt.where(Question.chapter_id.in_(chapter_ids))
        available=db.scalar(stmt) or 0
        missing=max(0,required-available)
        ok &= missing==0
        report.append({"difficulty_id":difficulty_id,"required":required,"available":available,"missing":missing})
    return ok,report

def generate_exam(db,name,chapter_ids,quotas):
    ok,report=preflight(db,chapter_ids,quotas)
    if not ok: raise ValueError({"message":"Không đủ câu hỏi để tạo đề.","requirements":report})
    selected=[]
    for did,required in quotas.items():
        stmt=select(Question).where(Question.is_active==True,Question.difficulty_id==did)
        if chapter_ids: stmt=stmt.where(Question.chapter_id.in_(chapter_ids))
        pool=list(db.scalars(stmt).all()); random.shuffle(pool); selected += pool[:required]
    random.shuffle(selected)
    exam=Exam(exam_code="EX"+datetime.now().strftime("%Y%m%d%H%M%S%f"),name=name or "Đề kiểm tra",total_questions=len(selected))
    db.add(exam); db.flush()
    for n,q in enumerate(selected,1):
        eq=ExamQuestion(exam_id=exam.id,question_id=q.id,question_number=n); db.add(eq); db.flush()
        opts=list(db.scalars(select(QuestionOption).where(QuestionOption.question_id==q.id)).all()); random.shuffle(opts)
        for i,o in enumerate(opts):
            db.add(ExamQuestionOption(exam_question_id=eq.id,source_option_id=o.id,display_key=LETTERS[i],display_order=i+1))
        db.add(QuestionUsage(question_id=q.id,exam_id=exam.id))
    db.commit(); return exam.id

def shuffle_exam(db,exam_id):
    eqs=list(db.scalars(select(ExamQuestion).where(ExamQuestion.exam_id==exam_id)).all()); random.shuffle(eqs)
    for i,eq in enumerate(eqs,1): eq.question_number=i
    for eq in eqs:
        opts=list(db.scalars(select(ExamQuestionOption).where(ExamQuestionOption.exam_question_id==eq.id)).all()); random.shuffle(opts)
        for i,o in enumerate(opts): o.display_key=LETTERS[i]; o.display_order=i+1
    db.commit()
