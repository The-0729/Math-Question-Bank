import random
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import delete,select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Chapter,Exam,ExamQuestion,ExamQuestionOption,Question,QuestionOption,QuestionUsage
from ..services.exam import preflight,generate_exam,shuffle_exam
router=APIRouter(prefix="/api/exams",tags=["exams"])
class ExamRequest(BaseModel):
    name:str|None=None
    chapter_ids:list[int]=[]
    easy:int=Field(ge=0)
    medium:int=Field(ge=0)
    hard:int=Field(ge=0)
class ReplacementRequest(BaseModel):
    question_id:int

@router.post("/preflight")
def check(p:ExamRequest,db:Session=Depends(get_db)):
    ok,r=preflight(db,p.chapter_ids,{1:p.easy,2:p.medium,3:p.hard});return {"can_generate":ok,"requirements":r}
@router.post("")
def create(p:ExamRequest,db:Session=Depends(get_db)):
    try: return {"exam_id":generate_exam(db,p.name,p.chapter_ids,{1:p.easy,2:p.medium,3:p.hard})}
    except ValueError as e: raise HTTPException(400,str(e))
@router.get("")
def list_exams(db:Session=Depends(get_db)):
    exams=db.scalars(select(Exam).order_by(Exam.created_at.desc(),Exam.id.desc())).all()
    out=[]
    for exam in exams:
        chapter_ids=db.scalars(select(Question.chapter_id).join(ExamQuestion,ExamQuestion.question_id==Question.id).where(ExamQuestion.exam_id==exam.id).distinct()).all()
        chapters=db.scalars(select(Chapter).where(Chapter.id.in_(chapter_ids)).order_by(Chapter.display_order,Chapter.id)).all() if chapter_ids else []
        out.append({"id":exam.id,"exam_code":exam.exam_code,"name":exam.name,"total_questions":exam.total_questions,"created_at":exam.created_at.isoformat(),"chapters":[chapter.name for chapter in chapters]})
    return out
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
        out.append({"id":eq.id,"number":eq.question_number,"question_code":q.question_code,"content":q.content,"chapter_id":q.chapter_id,"difficulty_id":q.difficulty_id,"options":opts,"answer":answer})
    return {"id":exam.id,"name":exam.name,"questions":out}
@router.get("/{exam_id}/questions/{exam_question_id}/candidates")
def replacement_candidates(exam_id:int,exam_question_id:int,db:Session=Depends(get_db)):
    exam_question=db.get(ExamQuestion,exam_question_id)
    if not exam_question or exam_question.exam_id!=exam_id: raise HTTPException(404,"Không tìm thấy câu trong đề.")
    current=db.get(Question,exam_question.question_id)
    used_questions=select(ExamQuestion.question_id).where(ExamQuestion.exam_id==exam_id)
    rows=db.execute(select(Question,Chapter.code).outerjoin(Chapter,Chapter.id==Question.chapter_id).where(Question.is_active==True,Question.difficulty_id==current.difficulty_id,Question.id.not_in(used_questions)).order_by(Question.chapter_id!=current.chapter_id,Question.question_code)).all()
    return [{"id":question.id,"question_code":question.question_code,"content":question.content,"chapter_code":chapter_code or "Chưa phân chương","same_chapter":question.chapter_id==current.chapter_id} for question,chapter_code in rows]
@router.put("/{exam_id}/questions/{exam_question_id}")
def replace_exam_question(exam_id:int,exam_question_id:int,p:ReplacementRequest,db:Session=Depends(get_db)):
    exam_question=db.get(ExamQuestion,exam_question_id)
    if not exam_question or exam_question.exam_id!=exam_id: raise HTTPException(404,"Không tìm thấy câu trong đề.")
    current=db.get(Question,exam_question.question_id)
    replacement=db.get(Question,p.question_id)
    if not replacement or not replacement.is_active: raise HTTPException(404,"Không tìm thấy câu hỏi thay thế.")
    if replacement.id==current.id: raise HTTPException(400,"Hãy chọn một câu hỏi khác.")
    if replacement.difficulty_id!=current.difficulty_id: raise HTTPException(400,"Câu thay thế phải cùng độ khó.")
    duplicate=db.scalar(select(ExamQuestion.id).where(ExamQuestion.exam_id==exam_id,ExamQuestion.id!=exam_question_id,ExamQuestion.question_id==replacement.id))
    if duplicate: raise HTTPException(400,"Câu hỏi này đã có trong đề.")
    db.execute(delete(ExamQuestionOption).where(ExamQuestionOption.exam_question_id==exam_question.id))
    db.execute(delete(QuestionUsage).where(QuestionUsage.exam_id==exam_id,QuestionUsage.question_id==current.id))
    exam_question.question_id=replacement.id
    options=list(db.scalars(select(QuestionOption).where(QuestionOption.question_id==replacement.id)).all())
    random.shuffle(options)
    for index,option in enumerate(options):
        db.add(ExamQuestionOption(exam_question_id=exam_question.id,source_option_id=option.id,display_key="ABCD"[index],display_order=index+1))
    db.add(QuestionUsage(question_id=replacement.id,exam_id=exam_id))
    db.commit()
    return {"ok":True}
@router.delete("/{exam_id}")
def delete_exam(exam_id:int,db:Session=Depends(get_db)):
    exam=db.get(Exam,exam_id)
    if not exam: raise HTTPException(404,"Không tìm thấy đề.")
    exam_questions=list(db.scalars(select(ExamQuestion.id).where(ExamQuestion.exam_id==exam_id)).all())
    if exam_questions:
        db.execute(delete(ExamQuestionOption).where(ExamQuestionOption.exam_question_id.in_(exam_questions)))
        db.execute(delete(ExamQuestion).where(ExamQuestion.exam_id==exam_id))
    db.execute(delete(QuestionUsage).where(QuestionUsage.exam_id==exam_id))
    db.delete(exam);db.commit()
    return {"ok":True}
