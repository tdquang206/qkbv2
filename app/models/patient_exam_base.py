from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship, declared_attr
from datetime import date, datetime

class SoftDeleteMixin:
    deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self, session=None):
        self.deleted = True
        self.deleted_at = datetime.now().astimezone()
        if session is not None:
            session.add(self)


class Parent(SoftDeleteMixin, Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    note = Column(String, nullable=True)
    last_visit = Column(DateTime,nullable=True)
    expected_date = Column(Date, nullable=True)
    deleted = Column(Boolean, default=False)

    # 1 parent - many kid - many exam
    kids = relationship("Kid", back_populates="parent")
    exams = relationship("Exam", back_populates="parent")
    
class Kid(SoftDeleteMixin, Base):
    __tablename__ = "kids"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=True)
    name = Column(String)
    birthday = Column(DateTime, nullable=True)
    note = Column(String, nullable=True)
    deleted = Column(Boolean, default=False)

    # 1 kid - may exams
    exams = relationship("Exam", back_populates="kid")
    parent = relationship("Parent", back_populates="kids")

class Exam(SoftDeleteMixin, Base):
    __tablename__ = "exams"
    id = Column(String, primary_key=True)  # use UUID string
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False, index=True)
    kid_id = Column(Integer, ForeignKey("kids.id"), nullable=True)
    exam_time = Column(DateTime, nullable=False)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    history = Column(String, nullable=True)
    drugs = Column(JSON, nullable=True, default=list)
    reexam_date = Column(Date, nullable=True)
    paid_status = Column(Boolean, default=False)
    create_at = Column(DateTime, default = datetime.now().astimezone())
    update_at = Column(DateTime, nullable=True)
    note = Column(String, nullable=True)
    deleted = Column(Boolean, default=False)

    # 1 exam - 1 kid - 1 parent
    kid = relationship("Kid", back_populates="exams")
    parent = relationship("Parent", back_populates="exams")
    images = relationship("ExamImage", back_populates="exam")

class ExamImage(Base):
    __tablename__ = "exam_images"
    id = Column(String, primary_key=True)  # uuid
    exam_id = Column(String, ForeignKey("exams.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)        # original filename
    storage_path = Column(String, nullable=False)    # path or object key
    url = Column(String, nullable=True)              # optional public URL or cached signed url
    mimetype = Column(String, nullable=True)
    size = Column(Integer, nullable=True)            # bytes
    order = Column(Integer, nullable=True)           # image number / ordering
    created_at = Column(DateTime, default=datetime.now().astimezone())
    deleted = Column(Boolean, default=False)
    # relationship
    exam = relationship("Exam", back_populates="images")
    
    