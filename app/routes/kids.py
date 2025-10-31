from __future__ import annotations
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from datetime import datetime, date
from uuid import uuid4

from app.database import get_session
from app.models.patient_exam_base import Parent, Kid, Exam, ExamImage, SoftDeleteMixin

templates = Jinja2Templates(directory="app/templates")

def get_db():
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

class KidBase(BaseModel):
    name: str
    parent_id: int
    birthday: Optional[datetime] = None
    note: Optional[str] = None
    deleted: Optional[bool] = False

    @field_validator("birthday", mode="before") 
    def parse_dates(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, (datetime, date)):
            return v
        # accept ISO or dd/mm/yyyy
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                if "T" in fmt:
                    return datetime.fromisoformat(v)
                if fmt == "%Y-%m-%d":
                    return datetime.strptime(v, fmt).date()
                return datetime.strptime(v, fmt).date()
            except Exception:
                continue
        raise ValueError("invalid date format")

class KidCreate(KidBase):
    parent_id: int
    

class KidUpdate(BaseModel):
    id: int
    parent_id: Optional[int] = None
    name: str
    birthday: Optional[str] = None
    parent_name: Optional[str] = None
    parent_last_visit: Optional[str] = None
    deleted: bool = False

    @field_validator("birthday", mode="before") 
    def parse_dates(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, (datetime, date)):
            return v
        # accept ISO or dd/mm/yyyy
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                if "T" in fmt:
                    return datetime.fromisoformat(v)
                if fmt == "%Y-%m-%d":
                    return datetime.strptime(v, fmt).date()
                return datetime.strptime(v, fmt).date()
            except Exception:
                continue
        raise ValueError("invalid date format")

class KidRead(BaseModel):
    id: int
    parent_id: Optional[int] = None
    name: str
    birthday: Optional[str] = None
    parent_name: Optional[str] = None
    parent_last_visit: Optional[str] = None
    deleted: bool = False
    
    model_config = {"from_attributes": True}

# CRUD code
def create_kid_db(db: Session, payload: KidCreate):
    from app.models.patient_exam_base import Kid, Parent
    parent = db.query(Parent).filter(Parent.id == payload.parent_id, Parent.deleted == False).first()
    if not parent:
        raise HTTPException(404, "Parent not found")

    existing = db.query(Kid).filter(Kid.name == payload.name, Kid.birthday == payload.birthday).first()
    if existing:
        if existing.deleted:
            # restore
            existing.deleted = False
            existing.name = payload.name
            existing.birthday = payload.birthday
            existing.note = payload.note
            existing.parent_id = payload.parent_id
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=400, detail="Kid already exists")

    kid = Kid(
        name=payload.name,
        birthday=payload.birthday,
        note = payload.note,
        parent_id = payload.parent_id,
        deleted = False,
    )
    db.add(kid)
    db.commit()
    db.refresh(kid)
    return kid

# router
router = APIRouter(prefix="/kids", tags=["kids"])

@router.post("", response_model=KidRead, status_code=status.HTTP_201_CREATED)
def create_kid(payload: KidCreate, db: Session = Depends(get_db), ):
    kid = create_kid_db(db, payload)
    return KidRead.model_validate(kid)

@router.post("/edit/{kid_id}")
def edit_kid(kid_id: int, payload: KidUpdate, db: Session = Depends(get_db), ):
    kid = db.query(Kid).filter(Kid.id == kid_id).first()
    if not kid:
        return RedirectResponse(url="/kids", status_code=303)
    
        # update fields
    kid.name = payload.name
    kid.birthday = payload.birthday
    kid.parent_id = payload.parent_id
    kid.parent_name = payload.parent_name
    kid.parent_last_visit = payload.parent_last_visit
    kid.deleted = payload.deleted

    db.add(kid)
    db.commit()
    db.refresh(kid)

    return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/edit/{kid_id}", name="edit_kid_form")
def edit_kid_form(request: Request, kid_id: int, db: Session = Depends(get_db)):
    kid = db.query(Kid).filter(Kid.id == kid_id).first()
    if not kid:
        return RedirectResponse(url="/kids", status_code=303)
    return templates.TemplateResponse(
        "edit_kid.html",
        {"request": request, "kid": kid}
    )






    
            
        