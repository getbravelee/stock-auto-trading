from fastapi import FastAPI
from app.api.endpoints.auth_router import auth_router
from app.api.endpoints.trade_router import trade_router
from app.api.endpoints.auto_trade_router import auto_trade_router

# .env 파일 로드 (가장 먼저 수행)
from dotenv import load_dotenv
load_dotenv() 

# 🟢 자동 매매 전략 상수 정의
BUY_QUANTITY = 1  # 🚨 요청하신 테스트 주문 수량 (1주)
# 🚨 8%, 10%, 12% 하락 레벨 (내림차순 정렬 필수 - 깊은 하락부터 확인)
DIP_LEVELS = [0.12, 0.10, 0.08]

# 1. FastAPI 애플리케이션 초기화
app = FastAPI(
    title="키움증권 REST API 서버",
    version="1.0.0",
    description="FastAPI 기반 키움증권 인증 및 거래 서버"
)

# 2. 라우터 등록
app.include_router(auth_router)
app.include_router(trade_router)
app.include_router(auto_trade_router)



# 3. 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    return {"app_name": app.title, "version": app.version, "status": "Running"}

# 이전의 `/hello/{name}` 엔드포인트는 제거하거나 적절히 활용하세요.
