# app/models/ki_models.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class KITokenRequest:
    """한투 토큰 발급 요청 바디"""
    grant_type: str = "client_credentials"
    appkey: str = field(default="")
    appsecret: str = field(default="")

@dataclass
class KITokenResponse:
    """한투 토큰 발급 성공 응답"""
    access_token: str
    token_type: str
    expires_in: int  # 유효기간(초)
    access_token_token_expired: str  # 유효기간(일시)

@dataclass
class KIApprovalKeyResponse:
    """한투 실시간 키 발급 성공 응답"""
    approval_key: str

class KIEndpoints:
    """한국투자증권 API 경로 정의"""
    # REST API 기본 URL (모의투자)
    BASE_URL = "https://openapivts.koreainvestment.com:29443"
    TOKEN_URL = f"{BASE_URL}/oauth2/tokenP"
    WEBSOCKET_KEY_URL = f"{BASE_URL}/oauth2/Approval"
    WEBSOCKET_URL = "ws://ops.koreainvestment.com:21000/tryitout/H0STASP0"

@dataclass
class KIApprovalKeyResponse:
    """한투 실시간 키 발급 성공 응답"""
    approval_key: str