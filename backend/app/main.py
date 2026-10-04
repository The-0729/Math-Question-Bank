from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .db.database import Base,engine,SessionLocal
from .db.models import Chapter,Difficulty
from .api.chapters import router as chapters_router
from .api.questions import router as questions_router
from .api.exams import router as exams_router
from .api.inspector import router as inspector_router
app=FastAPI(title="Math Question Bank V0.1")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
Base.metadata.create_all(bind=engine)
with engine.begin() as connection:
    question_columns={row[1] for row in connection.exec_driver_sql("PRAGMA table_info(questions)")}
    if "updated_at" not in question_columns:
        connection.exec_driver_sql("ALTER TABLE questions ADD COLUMN updated_at DATETIME")
db=SessionLocal()
if not db.scalar(select(Difficulty).where(Difficulty.id==1)):
    db.add_all([Difficulty(id=1,code="EASY",name="Easy",display_order=1),Difficulty(id=2,code="MEDIUM",name="Medium",display_order=2),Difficulty(id=3,code="HARD",name="Hard",display_order=3)]);db.commit()
if not db.scalar(select(Chapter.id).limit(1)):
    db.add_all([Chapter(code=f"CH{i}",name=name,display_order=i) for i,name in enumerate(["Căn bậc hai. Căn bậc ba","Hàm số bậc nhất và bậc hai","Hệ thức lượng trong tam giác vuông","Góc với đường tròn","Đường tròn","Tam giác đồng dạng","Một số yếu tố thống kê và xác suất","Hình học không gian"],1)]);db.commit()
db.close()
@app.get("/api/health")
def health(): return {"status":"ok"}
@app.get("/api/difficulties")
def difficulties(): return [{"id":1,"code":"EASY","name":"Easy"},{"id":2,"code":"MEDIUM","name":"Medium"},{"id":3,"code":"HARD","name":"Hard"}]
app.include_router(chapters_router);app.include_router(questions_router);app.include_router(exams_router);app.include_router(inspector_router)
