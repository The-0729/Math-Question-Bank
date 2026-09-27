from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Question,QuestionOption
from ..services.content import validate_content
router=APIRouter(prefix="/api/questions",tags=["questions"])
class OptionIn(BaseModel):
    key:str
    content:str
    is_correct:bool=False
class QuestionIn(BaseModel):
    chapter_id:int
    difficulty_id:int
    content:str
    explanation_content:str|None=None
    is_priority:bool=False
    options:list[OptionIn]=Field(min_length=4,max_length=4)

def next_code(db):
    n=db.query(Question).count()+1
    while db.scalar(select(Question).where(Question.question_code==f"Q{n:04d}")): n+=1
    return f"Q{n:04d}"

@router.get("")
def list_questions(db:Session=Depends(get_db)):
    out=[]
    for q in db.scalars(select(Question).where(Question.is_active==True).order_by(Question.id.desc())).all():
        opts=list(db.scalars(select(QuestionOption).where(QuestionOption.question_id==q.id).order_by(QuestionOption.display_order)).all())
        out.append({"id":q.id,"question_code":q.question_code,"chapter_id":q.chapter_id,"difficulty_id":q.difficulty_id,"content":q.content,"explanation_content":q.explanation_content,"is_priority":q.is_priority,"options":[{"key":o.option_key,"content":o.content,"is_correct":o.is_correct} for o in opts]})
    return out

@router.post("")
def create_question(p:QuestionIn,db:Session=Depends(get_db)):
    try:
        validate_content(p.content)
        for o in p.options: validate_content(o.content)
        if p.explanation_content: validate_content(p.explanation_content)
    except ValueError as e: raise HTTPException(400,str(e))
    if sum(o.is_correct for o in p.options)!=1: raise HTTPException(400,"Phải có đúng 1 đáp án đúng.")
    q=Question(question_code=next_code(db),chapter_id=p.chapter_id,difficulty_id=p.difficulty_id,content=p.content,explanation_content=p.explanation_content,is_priority=p.is_priority)
    db.add(q);db.flush()
    for i,o in enumerate(p.options): db.add(QuestionOption(question_id=q.id,option_key=o.key,content=o.content,is_correct=o.is_correct,display_order=i+1))
    db.commit();return {"id":q.id,"question_code":q.question_code}

@router.put("/{question_id}")
def update_question(question_id:int,p:QuestionIn,db:Session=Depends(get_db)):
    q=db.get(Question,question_id)
    if not q or not q.is_active: raise HTTPException(404,"Không tìm thấy câu hỏi.")
    try:
        validate_content(p.content)
        for o in p.options: validate_content(o.content)
        if p.explanation_content: validate_content(p.explanation_content)
    except ValueError as e: raise HTTPException(400,str(e))
    if sum(o.is_correct for o in p.options)!=1: raise HTTPException(400,"Phải có đúng 1 đáp án đúng.")
    q.chapter_id=p.chapter_id;q.difficulty_id=p.difficulty_id;q.content=p.content;q.explanation_content=p.explanation_content;q.is_priority=p.is_priority
    old=list(db.scalars(select(QuestionOption).where(QuestionOption.question_id==q.id)).all())
    for option in old: db.delete(option)
    db.flush()
    for i,o in enumerate(p.options): db.add(QuestionOption(question_id=q.id,option_key=o.key,content=o.content,is_correct=o.is_correct,display_order=i+1))
    db.commit();return {"id":q.id,"question_code":q.question_code}

@router.delete("/{question_id}")
def delete_question(question_id:int,db:Session=Depends(get_db)):
    q=db.get(Question,question_id)
    if not q: raise HTTPException(404,"Không tìm thấy câu hỏi.")
    q.is_active=False;db.commit();return {"ok":True}
