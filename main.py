from fastapi import FastAPI, Depends

from app.routers import users, auth

from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import text

app = FastAPI(
    title="PromptPix server works"
)

app.include_router(users.router)
app.include_router(auth.router)


@app.get("/")
def root(db: Session = Depends(get_db)):
    ver = db.execute(text("SELECT version()"))
    return {
        "message": "PromptPix server works",
        "version": ver.scalar()
    }
