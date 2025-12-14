# app/clients/ki_client.py
import requests
from typing import Dict, Any
from dataclasses import asdict

from ..models.ki_models import KITokenRequest, KIEndpoints


class KIRestClient:
    """한국투자증권(KI) REST API 통신 클라이언트."""

    def __init__(self):
        self.token_url = KIEndpoints.TOKEN_URL
        self.approval_url = KIEndpoints.WEBSOCKET_KEY_URL

    def _request(self, method: str, url: str, headers: Dict[str, str] = None, json_data: Dict[str, Any] = None) -> Dict[
        str, Any]:
        """HTTP 요청 처리 및 공통 예외 처리"""
        try:
            response = requests.request(method, url, headers=headers, json=json_data, timeout=10)

            if response.status_code != 200:
                error_details = response.json() if response.content else {"error": "응답 내용 없음"}
                raise requests.HTTPError(f"HTTP 통신 실패. 상태코드: {response.status_code}. 상세: {error_details}")

            response_data = response.json()

            if 'error_code' in response_data and response_data.get('error_code') != '0':  # 한투 에러 코드 확인
                raise ValueError(f"KI API 오류: {response_data.get('error_code')} - {response_data.get('message')}")

            return response_data

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"네트워크 오류 발생: {e}")

    def issue_access_token(self, appkey: str, secretkey: str) -> Dict[str, Any]:
        """접근 토큰 발급 요청"""
        request_data = KITokenRequest(appkey=appkey, appsecret=secretkey)
        headers: Dict[str, str] = {"content-type": "application/json"}

        raw_response = self._request(
            method="POST",
            url=self.token_url,
            headers=headers,
            json_data=asdict(request_data)
        )
        return raw_response

    def issue_websocket_key(self, token: str, appkey: str, secretkey: str) -> Dict[str, Any]:
        """실시간 (웹소켓) 접속 키 발급 요청 (접근 토큰 필요)"""

        if not token: raise ValueError("접근 토큰(access_token)이 필요합니다.")

        headers: Dict[str, str] = {
            "content-type": "application/json",
            "Authorization": f"Bearer {token}",
            "appkey": appkey,
            "appsecret": secretkey,
        }

        raw_response = self._request(
            method="POST",
            url=self.approval_url,
            headers=headers
        )
        return raw_response