from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modules.health.routes import router as health_router

app = FastAPI(title='Svelte-FastAPI Template')


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include Routers
app.include_router(health_router, prefix='/api/v1/health', tags=['health'])


@app.get('/')
async def root():
    return {'message': 'Welcome to Svelte-FastAPI Template'}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
