from pydantic import BaseModel
from datetime import datetime
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.base import Drugs, DrugsPurchase
from fastapi.templating import Jinja2Templates
from typing import List

from app.routes.drugs import get_db

router = APIRouter()

class DrugOut(BaseModel):
    id: int
    drug_sku: str
    drug_name: str
    drug_sell_price: float | None
    drug_purchase_price: float | None
    drug_stock: int | None

    class Config:
        orm_mode = True

@router.get("/api/drugs", response_model=List[DrugOut])
async def get_drugs(db: Session = Depends(get_db)):
    return db.query(Drugs).all()