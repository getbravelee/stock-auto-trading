import os

from fastapi import APIRouter, Depends, HTTPException
from app.services.auth_service import AuthService

auth_router = APIRouter(
    prefix="/auth/v1",
    tags=["Authentication"],
)


# 💡 종속성 주입: 서비스 객체를 엔드포인트에 주입합니다.
def get_auth_service():
    """인증 서비스 객체를 제공합니다."""
    # 클라이언트 객체 초기화 등 필요한 준비를 여기서 수행할 수 있습니다.
    return AuthService()


@auth_router.post("/issue-token")
async def issue_kiwoom_token(
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        app_key = os.getenv("APP_KEY")
        secret_key = os.getenv("SECRET_KEY")

        # 2. 서비스 로직 호출 (토큰 정보 딕셔너리를 받음)
        token_info = auth_service.issue_token(app_key=app_key, secret_key=secret_key)

        # 3. 사용자에게 반환
        return token_info


    except (ValueError, Exception) as e:  # Exception은 모든 오류를 포괄

        # HTTPError나 ConnectionError도 Exception 클래스를 상속받습니다.

        status_code = 401 if '토큰 발급 실패' in str(e) else 500

        raise HTTPException(

            status_code=status_code,

            detail=f"토큰 발급 실패: {str(e)}"

        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="서버 내부 오류 발생"
        )