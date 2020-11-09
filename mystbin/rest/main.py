from fastapi import FastAPI

from routers import pastes

app = FastAPI()

app.include_router(pastes.router)