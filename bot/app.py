from fastapi import FastAPI
from fastapi.responses import JSONResponse
from bot.healthcheck import healthcheck, ping

app = FastAPI(title="Notes Flow API")


@app.get("/healthcheck")
async def get_healthcheck():
    """Проверка здоровья приложения и подключения к AI API"""
    result = await healthcheck()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/ping")
async def get_ping():
    """Проверка подключения к AI модели"""
    result = await ping()
    status_code = 200 if result["status"] == "ok" else 503
    return JSONResponse(content=result, status_code=status_code)