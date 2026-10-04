from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Chapter,Question
router=APIRouter(prefix="/api/chapters",tags=["chapters"])
class ChapterIn(BaseModel):
    code:str
    name:str
    display_order:int=Field(default=0,ge=0)
@router.get("")
def list_chapters(db:Session=Depends(get_db)):
    return [{"id":c.id,"code":c.code,"name":c.name,"display_order":c.display_order} for c in db.scalars(select(Chapter).where(Chapter.is_active==True).order_by(Chapter.display_order,Chapter.id)).all()]
@router.post("")
def create_chapter(p:ChapterIn,db:Session=Depends(get_db)):
    c=Chapter(code=p.code,name=p.name,display_order=p.display_order);db.add(c);db.commit();db.refresh(c)
    return {"id":c.id,"code":c.code,"name":c.name}
@router.put("/{chapter_id}")
def update_chapter(chapter_id:int,p:ChapterIn,db:Session=Depends(get_db)):
    c=db.get(Chapter,chapter_id)
    if not c or not c.is_active: raise HTTPException(404,"Không tìm thấy chương.")
    c.code=p.code;c.name=p.name;c.display_order=p.display_order;db.commit()
    return {"id":c.id,"code":c.code,"name":c.name,"display_order":c.display_order}
@router.delete("/{chapter_id}")
def delete_chapter(chapter_id:int,db:Session=Depends(get_db)):
    c=db.get(Chapter,chapter_id)
    if not c or not c.is_active: raise HTTPException(404,"Không tìm thấy chương.")
    linked_questions=db.scalar(select(func.count(Question.id)).where(Question.chapter_id==chapter_id)) or 0
    if linked_questions:
        raise HTTPException(409,f"Không thể xóa chương {c.code} vì còn {linked_questions} câu hỏi liên kết. Hãy chuyển câu hỏi sang chương khác trước.")
    c.is_active=False;db.commit()
    return {"ok":True}
