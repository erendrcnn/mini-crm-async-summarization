from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from .core.config import settings
from .core.migrations import upgrade_head
import os
from .core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from .routers import auth, notes

app = FastAPI(
    title="Mini CRM API", 
    version="0.1.0",
    description="FastAPI mini CRM with async AI summarization"
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(notes.router, prefix="/notes", tags=["notes"])


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV, "version": "0.1.0"}


@app.get("/")
def root():
    return {
        "message": "Mini CRM API",
        "docs": "/docs",
        "health": "/health"
    }


@app.on_event("startup")
def maybe_run_migrations():
    if os.getenv("RUN_MIGRATIONS_ON_STARTUP", "false").lower() in {"1", "true", "yes"}:
        upgrade_head()
