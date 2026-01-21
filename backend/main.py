import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router
from core.config import settings
from core.database import init_db
from modules.compute.manager import get_manager
from modules.compute.service import cleanup_jobs_for_engine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def engine_cleanup_loop():
    """Periodically clean up idle engines."""
    while True:
        await asyncio.sleep(settings.engine_cleanup_interval)
        try:
            manager = get_manager()
            cleaned = manager.cleanup_idle_engines()
            if cleaned:
                for analysis_id in cleaned:
                    count = cleanup_jobs_for_engine(analysis_id)
                    logger.info(f'Cleaned up engine {analysis_id} and {count} associated jobs')
            else:
                logger.debug('No idle engines to clean up')
        except Exception as e:
            logger.error(f'Error in engine cleanup: {e}', exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting application...')
    await init_db()

    # Start background cleanup task
    cleanup_task = asyncio.create_task(engine_cleanup_loop())

    yield

    # Cancel cleanup task
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task

    # Cleanup compute processes on shutdown
    logger.info('Shutting down compute processes...')
    manager = get_manager()
    manager.shutdown_all()
    logger.info('Application shutdown complete')


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins_list,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
)

# Include Routers
app.include_router(router, tags=['api'])


@app.get('/')
async def root():
    return {'message': 'Welcome to Svelte-FastAPI Template'}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
