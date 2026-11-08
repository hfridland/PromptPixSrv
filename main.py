from fastapi import FastAPI, Depends

from app.routers import users, auth, image_trees

from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import text

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PromptPix server works"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(image_trees.router)


@app.get("/")
def root(db: Session = Depends(get_db)):
    ver = db.execute(text("SELECT version()"))
    return {
        "message": "PromptPix server works",
        "version": ver.scalar()
    }
