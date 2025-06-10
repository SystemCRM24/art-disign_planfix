# my_project/main.py
from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description=settings.PROJECT_DESCRIPTION,
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Bitrix Integration Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)