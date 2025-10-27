from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routes import drugs, home

app = FastAPI()
app.include_router(drugs.router)
app.include_router(home.router)

# api routes
app.include_router(drugs.router, prefix="/api", tags=["drugs"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")