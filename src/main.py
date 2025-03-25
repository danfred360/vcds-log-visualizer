import logging
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import Log, get_db, init_db
from .routers.log import log_router

load_dotenv(".env")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    init_db()
    logger.info("Database tables created successfully.")
    try:
        yield
    finally:
        logger.info("Shutting down the application...")


app = FastAPI(
    title="VCDS Log Visualizer",
    description="A web application for visualizing VCDS csv logs.",
    lifespan=lifespan,
)

allow_origins = [
    "http://localhost",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(log_router, prefix="/api/logs", tags=["logs"])

app.mount(
    "/static", app=StaticFiles(directory="src/client-app", html=True), name="static"
)
templates = Jinja2Templates(directory="src/client-app/templates")


@app.get("/", tags=["dashboard"])
async def dashboard(request: Request, db: Session = Depends(get_db)):
    logs = db.query(Log).all()
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "logs": logs}
    )


if __name__ == "__main__":
    print("Swagger page launched at http://127.0.0.1:57765/docs")
    uvicorn.run(app, host="127.0.0.1", port=57765)
