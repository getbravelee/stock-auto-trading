from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.requests import Request  # Request 객체 임포트
from typing import Optional
from asyncio import Task, create_task, CancelledError, sleep
import time

from typing_extensions import Any

from app.services.trade_service import TradeService

# main.py에 정의된 상수를 사용하기 위해 import를 대신하여, Request.app.state에서 접근하도록 구현 (가장 안전한 방법)

auto_trade_router = APIRouter(
    prefix="/autotrade",
    tags=["Auto Trade Scheduler"]
)


# 🚨 이 딕셔너리를 사용하여 현재 실행 중인 태스크를 관리합니다.
# FastAPI 앱 인스턴스에 직접 상태를 저장하는 것이 일반적입니다.
# (예: app.state.scanner_task = None)
# 여기서는 Request 객체를 통해 접근하는 방식으로 구현하겠습니다.

# ----------------------------------------------------------------------
# 주기적 스캐너 함수 (main.py의 로직을 그대로 가져옴)
# ----------------------------------------------------------------------
async def periodic_dip_scan(app_state: Any):  # app_state로 FastAPI의 상태를 받습니다.
    # TradeService 인스턴스 생성
    service = TradeService()

    # 상수를 app_state에서 가져옵니다. (main.py에서 app.state에 저장했다고 가정)
    # 🚨 만약 main.py에서 상수로 정의했다면, 여기서 글로벌 변수를 사용해야 합니다.
    # 여기서는 main.py에서 정의한 글로벌 변수를 그대로 사용한다고 가정하고 코드를 구성합니다.
    # 안전한 방법은 main.py의 상수를 이곳으로 옮기거나, Config 파일에서 관리하는 것입니다.

    # 🚨 주의: 아래 상수는 main.py의 상수를 가져왔다고 가정합니다.
    DIP_SCAN_PERIOD = 60
    BUY_QUANTITY = 1
    DIP_LEVELS = [0.08, 0.10, 0.12]

    while True:
        # 태스크가 취소되었는지 확인 (중지 요청 시)
        if hasattr(app_state, 'scanner_stop') and app_state.scanner_stop:
            print("🛑 [Auto-Trade] 중지 명령 수신. 백그라운드 스캐너 종료.")
            break

        start_time = time.time()

        try:
            print(f"\n--- ⏱️ 자동 스캐너 실행 시작: {time.time():.2f} ---")

            # 1. 스캔하여 눌림 구간 진입 종목 리스트 획득
            # 🚨 TradeService에 DIP_SCAN_LIMIT가 필요한 경우, 여기서 명시해야 합니다.
            found_dips = await service.scan_top_stocks_for_dip(limit=50)  # 50은 임시로 고정

            # ... (이하 주문 로직은 main.py의 로직과 동일하게 유지) ...
            if found_dips:
                for item in found_dips:
                    # ... (주문 및 상태 체크/업데이트 로직) ...
                    pass

        except CancelledError:
            print("🛑 [Auto-Trade] 태스크 취소됨. 정상 종료.")
            break
        except Exception as e:
            print(f"❌ 주기적 스캐너/주문 오류 발생: {e}")

        # 7. 실행 시간 측정 및 다음 실행까지 대기 시간 계산
        elapsed_time = time.time() - start_time
        sleep_duration = max(0, DIP_SCAN_PERIOD - elapsed_time)

        print(f"--- 분석 소요 시간: {elapsed_time:.2f}초. 다음 실행까지 {sleep_duration:.2f}초 대기 ---")
        await sleep(sleep_duration)


# ----------------------------------------------------------------------
# 라우터 엔드포인트
# ----------------------------------------------------------------------

@auto_trade_router.post("/start")
async def start_auto_trade(request: Request):
    """자동 매매 스캐너를 백그라운드에서 시작합니다."""

    # 이미 실행 중인지 확인
    if hasattr(request.app.state, 'scanner_task') and request.app.state.scanner_task:
        if not request.app.state.scanner_task.done():
            raise HTTPException(status_code=400, detail="자동 매매 스캐너가 이미 실행 중입니다.")

    # 기존 중지 플래그 초기화
    request.app.state.scanner_stop = False

    # 새로운 비동기 태스크 생성 및 저장
    # 여기서 periodic_dip_scan에 Request.app.state를 인수로 전달합니다.
    task = create_task(periodic_dip_scan(request.app.state))
    request.app.state.scanner_task = task

    print("✅ [Auto-Trade] 자동 매매 스캐너 실행 요청 성공.")
    return {"message": "자동 매매 스캐너를 백그라운드에서 시작했습니다.", "status": "running"}


@auto_trade_router.post("/stop")
async def stop_auto_trade(request: Request):
    """실행 중인 자동 매매 스캐너를 중지합니다."""

    # 실행 중인 태스크가 있는지 확인
    if not hasattr(request.app.state, 'scanner_task') or request.app.state.scanner_task is None:
        raise HTTPException(status_code=400, detail="실행 중인 자동 매매 스캐너가 없습니다.")

    task: Task = request.app.state.scanner_task

    if task.done():
        raise HTTPException(status_code=400, detail="자동 매매 스캐너가 이미 종료되었습니다.")

    # 1. Graceful Shutdown 플래그 설정
    request.app.state.scanner_stop = True

    # 2. 태스크 취소 요청 (즉시 종료)
    # task.cancel() # 강제 취소 대신, 다음 루프에서 종료되도록 플래그만 사용합니다.

    # 태스크 참조 제거 (선택 사항)
    request.app.state.scanner_task = None

    print("✅ [Auto-Trade] 자동 매매 스캐너 중지 요청 성공. 다음 주기에서 종료됩니다.")
    return {"message": "자동 매매 스캐너 중지 명령을 전송했습니다. 다음 주기에서 종료됩니다.", "status": "stopping"}


@auto_trade_router.get("/status")
async def get_auto_trade_status(request: Request):
    """자동 매매 스캐너의 현재 상태를 확인합니다."""

    if hasattr(request.app.state, 'scanner_task') and request.app.state.scanner_task:
        task: Task = request.app.state.scanner_task
        if task.done():
            status = "stopped (completed or error)"
        else:
            status = "running"
    else:
        status = "stopped (not started)"

    return {"status": status}