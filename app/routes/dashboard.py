from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import SessionLocal

from app.routes.parents import ParentRead, search_parents_db, get_parent_by_id
from app.routes.kids import KidRead
from app.models.patient_exam_base import Kid, Parent

def get_db():
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# include the template
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
def show_parents_and_kids(request: Request, db: Session = Depends(get_db)):
    # fetch from server
    parents_orm = search_parents_db(db, q=None, phone=None, limit=100)
    kids_q = db.query(Kid).options(joinedload(Kid.parent)).filter(Kid.deleted == False).limit(500).all()


    # Pydantic read model
    parents = [ParentRead.model_validate(p).model_dump() for p in parents_orm]
    kids = []
    for k in kids_q:
        pr = k.parent
        kids.append({
            "id": k.id,
            "parent_id": k.parent_id,
            "name": k.name,
            "birthday": k.birthday.isoformat() if k.birthday else None,
            "parent_name": pr.name if pr else None,
            "parent_last_visit": pr.last_visit.isoformat() if pr and pr.last_visit else None,
            "deleted": k.deleted,
        })



    
    return templates.TemplateResponse("parents_and_kids_list.html", {"request": request, "parents": parents, "kids": kids})
    

@router.get("/parents", response_model=list[ParentRead])
def parents_list(q: str | None = Query(None), limit: int = Query(200, ge=1, le=1000), db: Session = Depends(get_db)):

    parents = search_parents_db(db, q=q, phone=None, limit=limit)
    return [ParentRead.model_validate(p) for p in parents]

@router.get("/kids")
# Remove response_model for now until we fix the model
# @router.get("/kids", response_model=List[KidRead])
def kids_list(name: str | None = Query(None), limit: int = Query(500, ge=1, le=2000), db: Session = Depends(get_db)):
    """
    Return all kids (non-deleted) with their parent_id included.
    Consider adding pagination or server-side filtering for large datasets.
    """
    from app.models.patient_exam_base import Kid
    q = db.query(Kid).options(joinedload(Kid.parent)).filter(Kid.deleted == False)
    kids = q.limit(limit).all()
    # for each kid, build object with parent_name and parent_last_visit
    result = []
    for k in kids:
        pr = k.parent
        kid_data = KidRead(
            id=k.id,
            parent_id=k.parent_id,
            name=k.name,
            birthday=k.birthday.isoformat() if k.birthday else None,
            parent_name=pr.name if pr else None,
            parent_last_visit=pr.last_visit.isoformat() if pr and pr.last_visit else None,
            deleted=k.deleted
        )
        result.append(kid_data)
    return result


