from fastapi import FastAPI
from .routes.health import router as health_router
from .routes.tasks import router as tasks_router
app=FastAPI(title="UGAI Agent API",version="0.4.0"); app.include_router(health_router); app.include_router(tasks_router,prefix="/v1")
