from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.trade_service import TradeService  # TradeService 임포트
from app.models.kiwoom_schema import ChartAnalysisResult  # 분석 결과 모델 임포트

# APIRouter 객체 생성
trade_router = APIRouter(
    prefix="/trade/v1",  # 엔드포인트는 /trade/v1/으로 시작
    tags=["Trading & Account Analysis"],
)


# 💡 종속성 주입 함수: TradeService 객체를 생성하여 제공합니다.
def get_trade_service():
    """TradeService 객체를 주입하기 위한 함수."""
    return TradeService()


@trade_router.get("/analyze/peak/{stk_cd}", response_model=ChartAnalysisResult)
async def analyze_chart_for_peak(
        stk_cd: str,
        # Query 파라미터로 틱범위(예: 1분, 5분)를 받습니다. 기본값은 '1'분입니다.
        tic_scope: str = Query('1', description="틱범위 (1, 3, 5, 10, 15, 30, 45, 60 중 택1)"),
        trade_service: TradeService = Depends(get_trade_service)
):
    """
    특정 종목의 분봉 데이터를 조회하여 고점 대비 하락/반등 로직을 분석합니다.
    """
    try:
        # TradeService의 분석 메서드 호출
        result = trade_service.analyze_minute_chart_peak(stk_cd=stk_cd, tic_scope=tic_scope)
        return result

    except Exception as e:
        # 서비스 계층에서 발생한 예외를 HTTP 에러로 변환하여 반환
        print(f"ERROR in trade_router: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"차트 분석 요청 실패: {str(e)}"
        )


@trade_router.get("/scan/top-dip", response_model=List[Dict[str, Any]])
async def scan_for_dip_opportunities(
    limit: int = Query(50, description="조회할 거래대금 상위 종목 수"),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    거래대금 상위 N개 종목 중 8%~12% 눌림 구간에 진입한 종목 리스트를 반환합니다.
    """
    try:
        results = trade_service.scan_top_stocks_for_dip(limit=limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"스캐너 실행 실패: {e}"
        )