from fastapi import FastAPI
from api.predictAI import router as predict_router

app = FastAPI()
app.include_router(predict_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)