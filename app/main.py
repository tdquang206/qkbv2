from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routes import drugs, home, dashboard, parents, kids
from app.database import init_db

app = FastAPI()

# init db before include router
init_db()

app.include_router(drugs.router)
app.include_router(home.router)

# api routes
app.include_router(drugs.router, prefix="/api", tags=["drugs"])
app.include_router(dashboard.router)
app.include_router(parents.router)
app.include_router(kids.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/static/css", StaticFiles(directory="app/static/css"), name="static/css")
app.mount("/static/js", StaticFiles(directory="app/static/js"), name="static/js")

templates = Jinja2Templates(directory="app/templates")