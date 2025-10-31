from __future__ import annotations
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from datetime import datetime, date
from uuid import uuid4

from app.database import get_session
from app.models.patient_exam_base import Parent, Kid, Exam, ExamImage, SoftDeleteMixin

# mocup require_auth to addmin
# import os

# ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-secret")
# def require_admin(
#     authorization: Optional[str] = Header(None),
#     x_api_key: Optional[str] = Header(None),
# ):
#     """
#     Accepts:
#       - Authorization: Bearer <token>
#       - OR X-API-KEY: <token>
#     Only returns a simple admin user dict when token matches ADMIN_TOKEN.
#     Raises 401 if missing, 403 if invalid.
#     """
#     token = None
#     if authorization:
#         parts = authorization.split()
#         if len(parts) == 2 and parts[0].lower() == "bearer":
#             token = parts[1]
#     if not token and x_api_key:
#         token = x_api_key

#     if token is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

#     if token != ADMIN_TOKEN:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

#     # return a minimal "current user" object; adapt fields as needed
#     return {"id": "admin", "role": "admin", "name": "Local Admin"}


# real code form here
def get_db():
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic v2 
class ParentBase(BaseModel):
    phone: str = Field(..., min_length=10, max_length=10)
    name: str
    address: str
    note: Optional[str] = None
    last_visit: Optional[datetime] = None
    expected_date: Optional[datetime] = None
    deleted: Optional[bool] = False

    @field_validator("last_visit", "expected_date", mode="before")
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

# wat is this?
class ParentCreate(ParentBase):
    pass

class ParentUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    note: Optional[str] = None
    last_visit: Optional[datetime] = None
    expected_date: Optional[date] = None

    @field_validator("last_visit", "expected_date", mode="before")
    def parse_dates(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, (datetime, date)):
            return v
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                if "T" in fmt:
                    return datetime.fromisoformat(v)
                if fmt == "%d/%m/%Y":
                    return datetime.strptime(v, fmt).date()
                return datetime.strptime(v, fmt).date()
            except Exception:
                continue
        raise ValueError("invalid date format")
                   
class ParentRead(ParentBase):
    id: int
    deleted: bool = False
    model_config = {"from_attributes": True}

# CRUD
def get_parent_by_id(db: Session, parent_id: int):
    from app.models.patient_exam_base import Parent

    return db.query(Parent).filter(Parent.id == parent_id).first()

def get_parent_by_phone(db: Session, phone: str):
    from app.models.patient_exam_base import Parent

    return db.query(Parent).filter(Parent.phone == phone).first()


def search_parents_db(db: Session, q: Optional[str] = None, phone: Optional[str] = None, limit: int = 50):
    from app.models.patient_exam_base import Parent
    query = db.query(Parent).filter(Parent.deleted == False)
    if phone:
        query = query.filter(Parent.phone.ilike(f"%{phone}%"))
    if q:
        query = query.filter(Parent.name.ilike(f"%{q}%"))
    return query.order_by(Parent.id.desc()).limit(limit).all()

def create_parent_db(db: Session, payload: ParentCreate):
    from app.models.patient_exam_base import Parent
    existing = db.query(Parent).filter(Parent.phone == payload.phone).first()
    if existing:
        if existing.deleted:
            # restore instead of creating duplicate
            existing.deleted = False
            existing.name = payload.name
            existing.address = payload.address
            existing.note = payload.note
            existing.last_visit = payload.last_visit
            existing.expected_date = payload.expected_date
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=400, detail="Phone already exists")
    p = Parent(
        phone=payload.phone,
        name=payload.name,
        address=payload.address,
        note=payload.note,
        last_visit=payload.last_visit,
        expected_date=payload.expected_date,
        deleted=False,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def update_parent_db(db: Session, parent: "Parent", payload: ParentUpdate):
    # parent is ORM instance
    if payload.name is not None:
        parent.name = payload.name
    if payload.address is not None:
        parent.address = payload.address
    if payload.note is not None:
        parent.note = payload.note
    if payload.last_visit is not None:
        parent.last_visit = payload.last_visit
    if payload.expected_date is not None:
        parent.expected_date = payload.expected_date
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent

def soft_delete_parent_db(db: Session, parent: "Parent"):
    parent.deleted = True
    parent.deleted_at = datetime.utcnow() if hasattr(parent, "deleted_at") else None
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent

def restore_parent_db(db: Session, parent: "Parent"):
    parent.deleted = False
    if hasattr(parent, "deleted_at"):
        parent.deleted_at = None
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent

# ---------- Router ----------

router = APIRouter(prefix="/parents", tags=["parents"])

@router.get("/search", response_model=List[ParentRead])
def search_parents(q: Optional[str] = Query(None), phone: Optional[str] = Query(None), db: Session = Depends(get_db)):
    results = search_parents_db(db, q=q, phone=phone)
    return [ParentRead.model_validate(r) for r in results]

@router.get("/{parent_id}", response_model=ParentRead)
def read_parent(parent_id: int, db: Session = Depends(get_db)):
    p = get_parent_by_id(db, parent_id)
    if not p or getattr(p, "deleted", False):
        raise HTTPException(status_code=404, detail="Parent not found")
    return ParentRead.model_validate(p)

@router.post("", response_model=ParentRead, status_code=status.HTTP_201_CREATED)
def create_parent(payload: ParentCreate, db: Session = Depends(get_db), ):
    p = create_parent_db(db, payload)
    return ParentRead.model_validate(p)

@router.put("/{parent_id}", response_model=ParentRead)
def update_parent(parent_id: int, payload: ParentUpdate, db: Session = Depends(get_db), ):
    p = get_parent_by_id(db, parent_id)
    if not p or getattr(p, "deleted", False):
        raise HTTPException(status_code=404, detail="Parent not found")
    p = update_parent_db(db, p, payload)
    return ParentRead.model_validate(p)

@router.post("/{parent_id}/soft-delete", status_code=status.HTTP_200_OK)
def soft_delete_parent(parent_id: int, db: Session = Depends(get_db), ):
    p = get_parent_by_id(db, parent_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parent not found")
    soft_delete_parent_db(db, p)
    return {"ok": True}

@router.post("/{parent_id}/restore", status_code=status.HTTP_200_OK)
def restore_parent(parent_id: int, db: Session = Depends(get_db), ):
    p = get_parent_by_id(db, parent_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parent not found")
    restore_parent_db(db, p)
    return {"ok": True}
