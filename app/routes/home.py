from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def show(request: Request):
    return templates.TemplateResponse(
        "home_page.html",
        {"request": request}        
    )
