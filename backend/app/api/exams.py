from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Exam,ExamQuestion,ExamQuestionOption,Question,QuestionOption
from ..services.exam import preflight,generate_exam,shuffle_exam
router=APIRouter(prefix="/api/exams",tags=["exams"])
class ExamRequest(BaseModel):
    name:str|None=None
    chapter_ids:list[int]=[]
    easy:int=Field(ge=0)
    medium:int=Field(ge=0)
    hard:int=Field(ge=0)

@router.post("/preflight")
def check(p:ExamRequest,db:Session=Depends(get_db)):
    ok,r=preflight(db,p.chapter_ids,{1:p.easy,2:p.medium,3:p.hard});return {"can_generate":ok,"requirements":r}
@router.post("")
def create(p:ExamRequest,db:Session=Depends(get_db)):
    try: return {"exam_id":generate_exam(db,p.name,p.chapter_ids,{1:p.easy,2:p.medium,3:p.hard})}
    except ValueError as e: raise HTTPException(400,str(e))
@router.post("/{exam_id}/shuffle")
def shuffle(exam_id:int,db:Session=Depends(get_db)):
    if not db.get(Exam,exam_id): raise HTTPException(404,"Không tìm thấy đề.")
    shuffle_exam(db,exam_id);return {"ok":True}
@router.get("/{exam_id}")
def get_exam(exam_id:int,db:Session=Depends(get_db)):
    exam=db.get(Exam,exam_id)
    if not exam: raise HTTPException(404,"Không tìm thấy đề.")
    out=[]
    eqs=list(db.scalars(select(ExamQuestion).where(ExamQuestion.exam_id==exam_id).order_by(ExamQuestion.question_number)).all())
    for eq in eqs:
        q=db.get(Question,eq.question_id); maps=list(db.scalars(select(ExamQuestionOption).where(ExamQuestionOption.exam_question_id==eq.id).order_by(ExamQuestionOption.display_order)).all())
        opts=[];answer=None
        for m in maps:
            o=db.get(QuestionOption,m.source_option_id);opts.append({"key":m.display_key,"content":o.content})
            if o.is_correct:answer=m.display_key
        out.append({"number":eq.question_number,"question_code":q.question_code,"content":q.content,"options":opts,"answer":answer})
    return {"id":exam.id,"name":exam.name,"questions":out}
