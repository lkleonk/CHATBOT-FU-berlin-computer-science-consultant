import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    degrees_router,
    health_router,
    program_rules_router,
    session_router,
    tracing_router,
    usage_router,
)
from app.services.ssh_manager import SSHManager
from app.settings import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ssh_manager = SSHManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.API.TITLE, settings.API.VERSION)
    logger.info("Configured LLM provider: %s", settings.provider_name())

    if settings.is_fu_ollama():
        try:
            ssh_manager.start()
            tunnel_url = ssh_manager.get_base_url()
            if tunnel_url:
                settings.FU_OLLAMA.BASE_URL = tunnel_url
                logger.info("FU Ollama URL set to SSH tunnel: %s", settings.FU_OLLAMA.BASE_URL)
        except Exception:
            logger.exception("Failed to start SSH tunnel")

    logger.info("Active model: %s", settings.active_model_name())

    yield

    if settings.is_fu_ollama():
        ssh_manager.stop()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.API.TITLE,
    description=settings.API.DESCRIPTION,
    version=settings.API.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.DEPLOYMENT.CORS_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-RateLimit-Scope",
    ],
)

app.include_router(session_router)
app.include_router(program_rules_router)
app.include_router(degrees_router)
app.include_router(usage_router)
app.include_router(tracing_router)
app.include_router(health_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.DEPLOYMENT.HOSTNAME,
        port=settings.DEPLOYMENT.PORT,
        proxy_headers=True,
        forwarded_allow_ips=settings.DEPLOYMENT.FORWARDED_ALLOW_IPS,
    )
