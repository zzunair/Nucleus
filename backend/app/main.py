from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import REDIS_URL
from app.database import get_db
from app.routers import parse, resources


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_pool(RedisSettings.from_dsn(REDIS_URL))
    yield
    await app.state.redis.aclose()


app = FastAPI(title="Productivity App", lifespan=lifespan)

for router in (resources.clients, resources.projects, resources.tasks,
               resources.journal, resources.finance, parse.router):
    app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    return {"db": db.execute(text("SELECT 1")).scalar() == 1}
