# root/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import requests # requests 임포트 필요

# .env 파일 로드
load_dotenv() 

from app.api.ki_auth_router import ki_auth_router

app = FastAPI(title="Auto Trading System API")

app.include_router(ki_auth_router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Auto Trading System API is running."}

# if __name__ == "__main__":
#     # uvicorn main:app --reload
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# uvicorn main:app --reload