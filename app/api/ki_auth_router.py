# app/api/ki_auth_router.py
from fastapi import APIRouter, Depends, HTTPException
import requests

from ..services.ki_auth_service import KIAuthService

ki_auth_router = APIRouter(
    prefix="/ki/auth/v1",
    tags=["Korean Investment Authentication"],
)


# 종속성 주입 함수
def get_ki_auth_service():
    """한국투자증권 인증 서비스 객체를 제공합니다."""
    # 서비스 인스턴스를 생성하여 반환합니다.
    return KIAuthService()


@ki_auth_router.post("/issue-token", summary="접근 토큰 발급")
async def issue_ki_token(
        auth_service: KIAuthService = Depends(get_ki_auth_service)
):
    """한국투자증권 REST API 접근 토큰을 발급받습니다."""
    try:
        token_info = auth_service.issue_token()
        return token_info

    except (ValueError, ConnectionError, requests.HTTPError) as e:
        status_code = 401 if 'KI API 오류' in str(e) else 500
        raise HTTPException(
            status_code=status_code,
            detail=f"토큰 발급 실패: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"서버 내부 오류 발생: {type(e).__name__} - {str(e)}"
        )


@ki_auth_router.post("/issue-websocket-key", summary="실시간 (웹소켓) 키 발급")
async def issue_ki_websocket_key(
        access_token: str,  # 발급받은 접근 토큰을 인수로 받음
        auth_service: KIAuthService = Depends(get_ki_auth_service)
):
    """한국투자증권 실시간 웹소켓 접속 키(Approval Key)를 발급받습니다."""
    try:
        approval_key = auth_service.issue_websocket_key(token=access_token)

        return {"approval_key": approval_key}

    except (ValueError, ConnectionError, requests.HTTPError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"실시간 키 발급 실패: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"서버 내부 오류 발생: {type(e).__name__} - {str(e)}"
        )