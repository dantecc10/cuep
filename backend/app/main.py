from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.database import engine
from app.core.limiter import limiter
from app.routers import auth, users, materias, sedes, tutores, corridas, worker, two_factor, students

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(title="CUEP API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(two_factor.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(materias.router, prefix="/api/v1")
app.include_router(sedes.router, prefix="/api/v1")
app.include_router(tutores.router, prefix="/api/v1")
app.include_router(corridas.router, prefix="/api/v1")
app.include_router(worker.router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}
