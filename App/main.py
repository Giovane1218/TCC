from core import custom_openapi
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routers.authController import router as auth_router
from api.routers.predictController import router as predict_router
from api.routers.userController import router as user_router
from repositories.user_repository import initialize_authentication


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_authentication()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(predict_router)
app.include_router(auth_router)
app.include_router(user_router)


app.openapi = lambda: custom_openapi(app)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

    # validar senha
    # update usuario
    # delete usuario
    # ajustar token
    # arrumar docker
