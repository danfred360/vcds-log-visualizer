import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .routers.log import log_router

load_dotenv(".env")

app = FastAPI(
    title="VCDS Log Visualizer",
    description="A web application for visualizing VCDS csv logs.",
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

app.mount("/", app=StaticFiles(directory="src/client-app", html=True), name="root")


# @app.get("/", tags=["root"])
# async def redirect_to_swagger():
#     response = RedirectResponse(url="/docs")
#     return response


if __name__ == "__main__":
    print("Swagger page launched at http://127.0.0.1:57765/docs")
    uvicorn.run(app, host="127.0.0.1", port=57765)
