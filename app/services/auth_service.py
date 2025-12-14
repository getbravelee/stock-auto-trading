from app.client.auth_client import AuthClient
from typing import Dict


class AuthService:
    """
    토큰 발급과 관련된 비즈니스 로직 (키 관리, 토큰 만료 확인 등)을 처리합니다.
    """

    def __init__(self):
        # 클라이언트 객체를 서비스가 소유하고 호출합니다.
        self.client = AuthClient()

    def issue_token(self, app_key: str, secret_key: str) -> Dict[str, str]:
        """
        키를 검증하고, 클라이언트를 통해 토큰을 발급받아 필요한 정보를 반환합니다.
        """

        # 1. TODO: 토큰 만료 여부 확인 (캐싱 로직)

        # 2. 클라이언트 호출 (전체 응답 데이터를 받음)
        response_data = self.client.get_access_token(appkey=app_key, secretkey=secret_key)

        # 3. 토큰 정보를 추출하여 반환 (예시 응답 구조 활용)
        token_info = {
            "access_token": response_data.get("token"),
            "expires_dt": response_data.get("expires_dt"),
            "token_type": response_data.get("token_type")
        }

        # 4. TODO: 발급받은 토큰을 데이터베이스나 메모리에 저장/갱신 (token_type, expires_dt 포함)

        return token_info