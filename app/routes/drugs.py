from datetime import datetime
import json
from typing import List
from fastapi import APIRouter, Body, HTTPException, Request, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.base import Drugs, DrugsPurchase
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# get all drugs
@router.get("/drugs_list", response_class=HTMLResponse)
def show_all_drugs(request: Request, db: Session = Depends(get_db)):
    drugs = db.query(Drugs).all()

    return templates.TemplateResponse(
        "drugs_list.html",
        {"request": request, "drugs": drugs}
    )

# add new drugs
@router.post("/drugs_list")
def add_new_drug(
    request: Request,
    drug_sku: str = Form(...),
    drug_name: str = Form(...),
    drug_sell_price: float=Form(...),
    drug_purchase_price: float=Form(...),
    drug_stock: int=Form(...),
    db: Session = Depends(get_db)
):
    existing_drug = db.query(Drugs).filter(Drugs.drug_name == drug_name).first()
    if existing_drug:
        return JSONResponse(
            status_code=400,
            content={"message": f"Drug with name '{drug_name}' already exists"}
        )
    
    
    try:
        new_drug = Drugs(
            drug_sku=drug_sku,
            drug_name=drug_name,
            drug_sell_price=drug_sell_price,
            drug_purchase_price=drug_purchase_price,
            drug_stock=drug_stock    
        )
        db.add(new_drug)
        db.commit()
        db.refresh(new_drug)
    
        return RedirectResponse(url='drugs_list', status_code=303)
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=400,
            content={"message": f"Drug '{drug_name}' is existed"}
        )

@router.post("/import-drugs")
async def import_drugs_from_json(
    drugs_data: List[dict] = Body(default=...),
    db: Session = Depends(get_db)
):
    try:
        success_count = 0
        failed_count = 0
        
        for drug in drugs_data:
            try:
                existing_drug = db.query(Drugs).filter(Drugs.drug_name == drug["drug_name"]).first()
                if not existing_drug:
                    new_drug = Drugs(
                        drug_sku=drug["drug_sku"],
                        drug_name=drug["drug_name"],
                        drug_sell_price=float(drug["drug_sell_price"]),
                        drug_purchase_price=float(drug["drug_purchase_price"]),
                        drug_stock=int(drug["drug_stock"])
                    )
                    db.add(new_drug)
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                continue
        
        db.commit()
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Import completed. {success_count} drugs imported successfully, {failed_count} failed"
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drugs_purchase")
def show_form(request: Request, db: Session = Depends(get_db)):
    drugs = db.query(Drugs).all()
    purchases = db.query(DrugsPurchase).all()
    print("📊 Drugs in DB:", [d.drug_name for d in drugs])
    print("📊 Purchases in DB:", [(p.id, p.drug_id, p.drug_purchase_quantities) for p in purchases])

    return templates.TemplateResponse(
        "drugs_purchase.html",
        {"request": request, "drugs": drugs, "purchases": purchases}
    )

@router.post("/drugs_purchase")    
def add_purchase(
    request: Request,
    drug_id: int=Form(...),
    drug_purchase_quantities: int=Form(...),
    drug_purchase_subcost: int=Form(...),
    db: Session = Depends(get_db)
):
    print(f"Creating add purchase... object")
    new_purchase = DrugsPurchase(
        drug_id = drug_id,
        drug_purchase_quantities = drug_purchase_quantities,
        drug_purchase_subcost = drug_purchase_subcost,
        drug_purchase_purchase_date = datetime.now(),

        drug_purchase_paid_status=False
    )
    print(f"new purchase object created")
    db.add(new_purchase)
    
    db.commit()
    print(f"commmit done")
    db.refresh(new_purchase)
    
    return RedirectResponse(url="/drugs_purchase", status_code=303)