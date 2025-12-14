import requests
import json
from typing import Dict, Any

# 상수 정의
HOST = 'https://api.kiwoom.com'
TOKEN_ENDPOINT = '/oauth2/token'
TOKEN_URL = HOST + TOKEN_ENDPOINT


class AuthClient:
    """
    외부 시스템(키움증권)의 인증 API 통신을 담당하는 클라이언트 클래스.
    토큰 발급 요청 및 응답 처리에 집중합니다.
    """

    def __init__(self, host: str = HOST):
        """클라이언트 초기화. 통신 HOST를 설정할 수 있습니다."""
        self.token_url = host + TOKEN_ENDPOINT

    def get_access_token(self, appkey: str, secretkey: str) -> Dict[str, str]:
        """
        REST API 접근 토큰을 발급받아 응답 데이터를 딕셔너리로 반환합니다.

        # ... (이전의 Args, Returns, Raises 설명 유지)
        """
        if not appkey or not secretkey:
            raise ValueError("AppKey와 SecretKey는 필수 입력값입니다.")

        token_url = self.token_url  # self.token_url은 __init__에서 설정되어 있어야 함

        # 1. 요청 데이터 구성 (예시의 params와 동일)
        data: Dict[str, Any] = {
            'grant_type': 'client_credentials',
            'appkey': appkey,
            'secretkey': secretkey,
        }

        # 2. 헤더 구성 (예시와 동일)
        headers: Dict[str, str] = {
            'Content-Type': 'application/json;charset=UTF-8',
        }

        try:
            # 3. HTTP POST 요청 실행
            response = requests.post(token_url, headers=headers, json=data)

            # 4. HTTP 상태 코드 확인 및 예외 처리
            if response.status_code != 200:
                error_details = response.json() if response.content else {"error": "응답 내용 없음"}
                raise requests.HTTPError(f"토큰 발급 실패. HTTP 상태코드: {response.status_code}. 상세: {error_details}")

            # 5. JSON 응답 파싱
            response_data = response.json()

            # 6. 키움증권의 자체 응답 코드 확인
            if response_data.get('return_code') != 0:
                # 지정 단말기 오류 등 키움 API 자체 에러 처리
                raise ValueError(f"키움 API 오류: {response_data.get('return_msg', '알 수 없는 오류')}")

            # 7. 성공적으로 처리되었을 경우 전체 응답 반환
            return response_data

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"네트워크 오류로 토큰 발급에 실패했습니다: {e}")