from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Chapter(Base):
    __tablename__="chapters"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    code: Mapped[str]=mapped_column(String(50),unique=True,nullable=False)
    name: Mapped[str]=mapped_column(String(255),nullable=False)
    display_order: Mapped[int]=mapped_column(Integer,default=0)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Difficulty(Base):
    __tablename__="difficulty"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    code: Mapped[str]=mapped_column(String(20),unique=True,nullable=False)
    name: Mapped[str]=mapped_column(String(50),nullable=False)
    display_order: Mapped[int]=mapped_column(Integer,nullable=False)

class Question(Base):
    __tablename__="questions"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    question_code: Mapped[str]=mapped_column(String(20),unique=True,nullable=False)
    chapter_id: Mapped[int]=mapped_column(ForeignKey("chapters.id"),nullable=False)
    difficulty_id: Mapped[int]=mapped_column(ForeignKey("difficulty.id"),nullable=False)
    content: Mapped[str]=mapped_column(Text,nullable=False)
    explanation_content: Mapped[str|None]=mapped_column(Text)
    is_priority: Mapped[bool]=mapped_column(Boolean,default=False)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class QuestionOption(Base):
    __tablename__="question_options"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    question_id: Mapped[int]=mapped_column(ForeignKey("questions.id"),nullable=False)
    option_key: Mapped[str]=mapped_column(String(1),nullable=False)
    content: Mapped[str]=mapped_column(Text,nullable=False)
    is_correct: Mapped[bool]=mapped_column(Boolean,default=False)
    display_order: Mapped[int]=mapped_column(Integer,nullable=False)

class Exam(Base):
    __tablename__="exams"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    exam_code: Mapped[str]=mapped_column(String(50),unique=True,nullable=False)
    name: Mapped[str|None]=mapped_column(String(255))
    total_questions: Mapped[int]=mapped_column(Integer,nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class ExamQuestion(Base):
    __tablename__="exam_questions"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    exam_id: Mapped[int]=mapped_column(ForeignKey("exams.id"),nullable=False)
    question_id: Mapped[int]=mapped_column(ForeignKey("questions.id"),nullable=False)
    question_number: Mapped[int]=mapped_column(Integer,nullable=False)

class ExamQuestionOption(Base):
    __tablename__="exam_question_options"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    exam_question_id: Mapped[int]=mapped_column(ForeignKey("exam_questions.id"),nullable=False)
    source_option_id: Mapped[int]=mapped_column(ForeignKey("question_options.id"),nullable=False)
    display_key: Mapped[str]=mapped_column(String(1),nullable=False)
    display_order: Mapped[int]=mapped_column(Integer,nullable=False)

class QuestionUsage(Base):
    __tablename__="question_usage"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    question_id: Mapped[int]=mapped_column(ForeignKey("questions.id"),nullable=False)
    exam_id: Mapped[int]=mapped_column(ForeignKey("exams.id"),nullable=False)
    used_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
