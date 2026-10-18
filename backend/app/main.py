# Application entry point
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.stocks import router as stocks_router

from app.core.config import settings
from app.core.logging import logger


from app.db.session import get_db


app = FastAPI(
    title=settings.app_name, 
    version=settings.app_version, 
    debug=settings.debug
)

app.include_router(health_router)
app.include_router(stocks_router)

@app.get("/")
def root():
    logger.info("Root endpoint called")
    
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
        "status": "running",
    }