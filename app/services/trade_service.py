import os
import asyncio
from typing import Dict, Any, List

# 가정: RestClient, AuthService, PeakTracker는 구현되어 있음
from app.client.rest_client import RestClient
from app.services.auth_service import AuthService
from app.services.peak_tracker import PeakTracker
from app.models.kiwoom_schema import MinPoleChartData, ChartAnalysisResult


class TradeService:
    def __init__(self):
        self.rest_client = RestClient()
        self.auth_service = AuthService()

        # 🟢 추가: 종목별 매수 이력을 저장하는 인메모리 캐시
        # { '종목코드': 가장 최근 매수가 실행된 하락률 (float, 예: 0.08) }
        self.order_status_cache: Dict[str, float] = {}

    def analyze_minute_chart_peak(self, stk_cd: str, tic_scope: str = '1') -> ChartAnalysisResult:
        """단일 종목의 분봉 데이터를 조회하고 PeakTracker 알고리즘을 적용합니다."""

        try:
            # 1. 토큰 가져오기 (FastAPI DI 또는 캐싱으로 대체될 수 있음)
            token_dict = self.auth_service.issue_token(
                app_key=os.getenv("APP_KEY"),
                secret_key=os.getenv("SECRET_KEY")
            )
            current_token = token_dict.get('access_token')
        except Exception as e:
            raise Exception(f"인증 오류: 토큰 발급 실패: {e}")

        # 2. 분봉 데이터 요청
        chart_data_api_response = self.rest_client.get_minute_chart_data(
            token=current_token,
            stk_cd=stk_cd,
            tic_scope=tic_scope
        )

        # 3. 데이터 정제 및 알고리즘 적용
        raw_bars: List[dict] = chart_data_api_response.get("stk_min_pole_chart_qry", [])
        bars = [MinPoleChartData.from_api_response(d) for d in reversed(raw_bars)]

        # 🚨 수정: PeakTracker 초기화 시 인수 제거
        tracker = PeakTracker()
        analysis_log: List[Dict[str, Any]] = []

        for bar in bars:
            # 🚨 수정: 고가, 저가, 종가를 모두 전달
            tracker.process_bar_data(
                high=bar.high_pric,
                low=bar.low_pric,
                close=bar.cur_prc
            )

            # 분석 상태를 확인하고 로그를 기록합니다.
            current_status = tracker.get_status()

            # 🚨 수정: 로그 엔트리 키를 영문으로 통일 (스캐너에서 필터링하기 위함)
            log_entry = {
                'time': bar.cntr_tm,
                'price': bar.cur_prc,
                'current_peak': current_status['기준 고점 (Peak)'],
                'zone_active': current_status['눌림 구간 진입 여부 (Zone Active)'],
                'zone_min_price': current_status['눌림 구간 최저점 (Zone Min Price)']
            }
            analysis_log.append(log_entry)

        final_status = tracker.get_status()
        return ChartAnalysisResult(
            symbol=stk_cd,
            peak_tracker_status=analysis_log,
            final_peak=final_status['기준 고점 (Peak)']
        )

    def scan_top_stocks_for_dip(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        거래대금 상위 limit개 종목 중 눌림 구간에 진입한 종목을 찾아 리스트로 반환합니다.
        """
        result_list = []

        # 1. 유효 토큰 가져오기
        try:
            token_dict = self.auth_service.issue_token(
                app_key=os.getenv("APP_KEY"),
                secret_key=os.getenv("SECRET_KEY")
            )
            current_token = token_dict.get('access_token')
        except Exception as e:
            print(f"FATAL ERROR: 토큰 발급 실패 - {e}")
            return []

        # 2. 거래대금 상위 종목 리스트 조회
        try:
            top_stocks = self.rest_client.get_top_trading_value(token=current_token)
        except Exception as e:
            print(f"ERROR: 거래대금 상위 종목 조회 실패 - {e}")
            return []

        # 3. 상위 N개 종목 코드 추출
        top_codes_with_name = [{'stk_cd': s['stk_cd'], 'stk_nm': s['stk_nm']} for s in top_stocks][:limit]

        print(f"INFO: 거래대금 상위 {len(top_codes_with_name)}개 종목 분석 시작.")

        # 4. 각 종목에 대해 분석
        for stock in top_codes_with_name:
            stk_cd = stock['stk_cd']
            stk_nm = stock['stk_nm']

            try:
                # analyze_minute_chart_peak 메서드 재사용 (5분봉 기준)
                analysis_result = self.analyze_minute_chart_peak(
                    stk_cd=stk_cd,
                    tic_scope='5'
                )

                # 5. 눌림 구간 진입 종목 필터링 (마지막 로그 확인)
                final_status_log = analysis_result.peak_tracker_status[
                    -1] if analysis_result.peak_tracker_status else None

                if final_status_log:
                    is_active = final_status_log.get('zone_active', False)

                    # 🟢 zone_active가 True인 경우 (눌림 구간 진입/유지 중)
                    if is_active is True:
                        result_list.append({
                            "stk_cd": stk_cd,
                            "stk_nm": stk_nm,
                            "current_peak": final_status_log['current_peak'],
                            "current_price": final_status_log['price'],
                            "zone_min_price": final_status_log['zone_min_price'],
                            "status": "IN_DIP_ZONE",
                            "time": final_status_log['time']
                        })

            except Exception as e:
                # 특정 종목 API 오류는 건너뛰고 다음 종목 진행
                print(f"WARN: 종목 {stk_cd} 분석 실패 - {e}")
                continue

        return result_list


    async def execute_buy_order(self, stk_cd: str, ord_qty: int) -> Dict[str, Any]:
        """자동 매수 주문을 실행하고 결과를 반환합니다."""
        if ord_qty <= 0:
            raise ValueError("주문 수량은 0보다 커야 합니다.")

        try:
            # 1. 유효 토큰 가져오기 (비동기 처리 가정)
            # 🚨 실제 환경에 맞게 토큰 획득 로직을 구현해야 합니다.
            # 예: token = await self.auth_service.get_valid_token()
            token = os.getenv("MY_KIWOOM_TOKEN")  # 임시 토큰 획득 가정

            # 2. 주문 API 호출
            order_result = await self.rest_client.stock_buy_order(
                token=token,
                stk_cd=stk_cd,
                ord_qty=ord_qty
            )

            # 3. 결과 반환
            return order_result

        except Exception as e:
            # 주문 실패 시 예외 처리
            print(f"FATAL: {stk_cd} 매수 주문 실패 - {e}")
            raise