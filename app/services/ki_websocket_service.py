# app/services/ki_websocket_service.py
import json
import threading
import time
from typing import Dict, Any, Optional

# 외부 라이브러리: 웹소켓 통신을 위해 필요합니다. (pip install websocket-client)
from websocket import create_connection, WebSocketApp

from ..models.ki_models import KIEndpoints, RealtimeSubscription


class KIWebSocketService:
    """
    한국투자증권 실시간 웹소켓 통신 서비스.
    approval_key를 사용하여 연결을 설정하고 실시간 시세를 구독합니다.
    """

    def __init__(self, approval_key: str, app_key: str, app_secret: str):
        self.approval_key = approval_key
        self.app_key = app_key
        self.app_secret = app_secret
        self.ws: Optional[WebSocketApp] = None
        self.is_running = False
        self.ws_thread: Optional[threading.Thread] = None

    # --- WebSocket 이벤트 핸들러 ---

    def _on_open(self, ws):
        """웹소켓 연결 성공 시 호출"""
        print("🟢 WebSocket 연결 성공")
        # 연결 후 즉시 구독 요청을 보내도 되지만, 외부에서 send_subscription_request를 호출하는 것이 더 유연합니다.

    def _on_message(self, ws, message: str):
        """웹소켓으로부터 메시지 수신 시 호출"""
        data = json.loads(message)

        # 1. 헤더/응답 메시지 처리
        if isinstance(data, dict) and 'header' in data:
            print(f"🟡 웹소켓 응답 수신: {data['body'].get('msg1', '구독 성공')}")

        # 2. 실시간 시세 데이터 처리
        elif isinstance(data, list) and len(data) == 2:
            # 실시간 데이터는 [헤더, 본문] 리스트 형태로 수신됩니다.
            header = data[0]['header']
            tr_id = header['tr_id']
            tr_key = header['tr_key']

            # 본문은 '|'로 구분된 문자열입니다.
            body_str = data[1]
            body_data = body_str.split('|')

            # TODO: tr_id에 따라 body_data를 파싱하는 로직 구현 (예: 체결가, 체결량 추출)

            # 임시 출력: 주식 체결가(H0STASP0) 기준, 현재가(0번 인덱스)
            if tr_id == "H0STASP0" and body_data:
                current_price = body_data[0]
                print(f"[{tr_id} {tr_key}] 실시간 체결가 수신: 현재가={current_price}")
            else:
                print(f"[{tr_id} {tr_key}] 원시 데이터 수신: {body_data}")

            # ⭐ 핵심: 이 데이터를 키움증권 주문 서비스로 전달하는 로직이 필요합니다.
            # self.order_service.process_realtime_data(tr_key, current_price)

        else:
            print(f"📦 기타 메시지: {data}")

    def _on_error(self, ws, error):
        """웹소켓 오류 발생 시 호출"""
        print(f"🔴 WebSocket 오류 발생: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """웹소켓 연결 종료 시 호출"""
        print(f"⚫ WebSocket 연결 종료: {close_status_code}, {close_msg}")
        self.is_running = False

    # --- 연결 관리 ---

    def start_connection(self):
        """웹소켓 연결을 별도 스레드에서 시작합니다."""
        if self.is_running:
            print("웹소켓 연결이 이미 실행 중입니다.")
            return

        self.is_running = True
        self.ws_thread = threading.Thread(target=self._run_forever)
        self.ws_thread.daemon = True  # 메인 스레드 종료 시 함께 종료
        self.ws_thread.start()
        print("🚀 WebSocket 연결 스레드 시작.")

    def _run_forever(self):
        """WebSocketApp을 실행하여 연결을 유지합니다."""
        self.ws = WebSocketApp(
            KIEndpoints.WEBSOCKET_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever()

    def close_connection(self):
        """웹소켓 연결을 종료합니다."""
        if self.ws:
            print("👋 웹소켓 연결 종료 요청...")
            self.ws.close()
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=1)

    # --- 구독/해지 요청 ---

    def send_subscription_request(self, subscription: RealtimeSubscription, is_subscribe: bool = True):
        """실시간 데이터 구독/해지 요청 전송"""

        # 연결 확인
        if not self.ws or not self.ws.sock or not self.ws.sock.connected:
            print("❌ 웹소켓 연결이 활성화되지 않았습니다. 요청 실패.")
            return

        # 요청 JSON 데이터 구성
        request_data = {
            "header": {
                "content-type": "application/json",
                "appkey": self.app_key,  # 생성자에서 받은 app_key
                # 웹소켓 요청 시 Access Token 대신 Approval Key만 사용해도 되는 경우가 많으나,
                # 한투 문서에 따라 Authorization 헤더를 포함할 수도 있습니다.
                # 여기서는 'approval_key'를 body에 넣는 표준 방식만 사용합니다.
                "custtype": "P",
                "tr_type": "1" if is_subscribe else "2",  # 1: 구독, 2: 해지
                "simul_yn": "N",
                "tr_id": subscription.tr_id,
                "tr_key": subscription.tr_key
            },
            "body": {
                "input": {
                    "approval_key": self.approval_key,  # 발급받은 실시간 키
                    "custtype": "P",
                    "ht_id": subscription.tr_id,
                    "fid_input_area": f"I|{subscription.tr_key}"  # 종목 코드 입력
                }
            }
        }

        try:
            self.ws.send(json.dumps(request_data))
            action = "구독 요청" if is_subscribe else "해지 요청"
            print(f"➡️ {action} 전송 성공: TRID={subscription.tr_id}, 종목={subscription.tr_key}")
        except Exception as e:
            print(f"❌ 구독 요청 전송 실패: {e}")