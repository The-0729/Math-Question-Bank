from fastapi import APIRouter,Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Chapter
router=APIRouter(prefix="/api/chapters",tags=["chapters"])
class ChapterIn(BaseModel):
    code:str
    name:str
@router.get("")
def list_chapters(db:Session=Depends(get_db)):
    return [{"id":c.id,"code":c.code,"name":c.name} for c in db.scalars(select(Chapter).where(Chapter.is_active==True).order_by(Chapter.display_order,Chapter.id)).all()]
@router.post("")
def create_chapter(p:ChapterIn,db:Session=Depends(get_db)):
    c=Chapter(code=p.code,name=p.name);db.add(c);db.commit();db.refresh(c)
    return {"id":c.id,"code":c.code,"name":c.name}
