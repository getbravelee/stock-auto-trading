# app/services/ki_auth_service.py
from typing import Dict
import os  # .env 로드를 위한 os 임포트

from ..clients.ki_client import KIRestClient
from ..models.ki_models import KITokenResponse, KIApprovalKeyResponse


class KIAuthService:
    """한국투자증권 토큰 및 키 발급과 관련된 비즈니스 로직을 처리합니다."""

    def __init__(self):
        self.client = KIRestClient()
        self.app_key = os.getenv("APP_KEY")
        self.secret_key = os.getenv("SECRET_KEY")

        if not self.app_key or not self.secret_key:
            raise ValueError("APP_KEY 또는 SECRET_KEY가 환경 변수에서 로드되지 않았습니다.")

    def issue_token(self) -> Dict[str, str]:
        """접근 토큰을 발급받아 필요한 정보를 딕셔너리로 반환합니다."""

        # 1. TODO: 토큰 만료 여부 확인 및 캐싱 로직 추가

        # 2. 클라이언트 호출
        response_data = self.client.issue_access_token(
            appkey=self.app_key,
            secretkey=self.secret_key
        )

        # 3. 데이터 모델로 변환 및 유효성 검증
        token_response = KITokenResponse(**response_data)

        # 4. 토큰 정보를 추출하여 반환
        token_info = {
            "access_token": token_response.access_token,
            "expires_in": token_response.expires_in,
            "expires_dt": token_response.access_token_token_expired
        }

        return token_info

    def issue_websocket_key(self, token: str) -> str:
        """실시간 키를 발급받아 approval_key 문자열을 반환합니다."""

        # 1. 클라이언트 호출
        response_data = self.client.issue_websocket_key(
            token=token,
            appkey=self.app_key,
            secretkey=self.secret_key
        )

        # 2. 데이터 모델로 변환 및 유효성 검증
        approval_response = KIApprovalKeyResponse(**response_data)

        return approval_response.approval_key