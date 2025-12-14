import requests
import json
from typing import Dict, Any, List

HOST = 'https://api.kiwoom.com'


class RestClient:
    """
    키움증권의 일반 REST API (차트, 잔고, 시세 등) 통신을 담당하는 클라이언트.
    """

    def __init__(self, host: str = HOST):
        self.host = host

    def get_minute_chart_data(self, token: str, stk_cd: str, tic_scope: str, upd_stkpc_tp: str = '1',
                              cont_yn: str = 'N', next_key: str = '') -> Dict[str, Any]:
        """
        주식분봉차트조회요청 (ka10080)을 처리합니다.
        """
        if not token or not stk_cd:
            raise ValueError("Access Token과 종목코드는 필수입니다.")

        endpoint = '/api/dostk/chart'
        url = self.host + endpoint

        # 1. 요청 데이터 구성
        data: Dict[str, str] = {
            'stk_cd': stk_cd,
            'tic_scope': tic_scope,
            'upd_stkpc_tp': upd_stkpc_tp,
        }

        # 2. header 데이터 구성
        headers: Dict[str, str] = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10080',  # TR명
        }

        try:
            # 3. HTTP POST 요청
            response = requests.post(url, headers=headers, json=data)

            # 4. HTTP 상태 코드 및 키움 자체 응답 코드 확인
            if response.status_code != 200:
                error_details = response.json() if response.content else {"error": "응답 내용 없음"}
                raise requests.HTTPError(f"차트 조회 실패. HTTP 상태코드: {response.status_code}. 상세: {error_details}")

            response_data = response.json()

            if response_data.get('return_code') != 0:
                raise ValueError(f"키움 API 오류: {response_data.get('return_msg', '알 수 없는 오류')}")

            return response_data

        except requests.exceptions.RequestException as e:
            # 네트워크 오류, 연결 문제 처리
            raise ConnectionError(f"네트워크 오류로 차트 조회에 실패했습니다: {e}")

    def get_top_trading_value(self, token: str) -> List[Dict[str, str]]:
        """
        거래대금 상위 종목 리스트 (ka10032)를 조회합니다.
        시장구분: 전체(000), 관리종목 포함(1), 거래소: 통합(3)으로 고정합니다.
        """
        endpoint = '/api/dostk/rkinfo'
        url = self.host + endpoint

        # 1. 요청 데이터 구성 (요청하신 조건: 전체, 관리종목 포함, 통합)
        data: Dict[str, str] = {
            'mrkt_tp': '000',  # 000: 전체
            'mang_stk_incls': '1',  # 1: 관리종목 포함
            'stex_tp': '3',  # 3: 통합
        }

        # 2. header 데이터 구성
        headers: Dict[str, str] = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'api-id': 'ka10032',
            # 연속 조회는 필요하지 않으므로 cont-yn, next-key 생략
        }

        try:
            response = requests.post(url, headers=headers, json=data)

            if response.status_code != 200:
                raise requests.HTTPError(f"거래대금 상위 조회 실패. HTTP 상태코드: {response.status_code}")

            response_data = response.json()

            if response_data.get('return_code') != 0:
                raise ValueError(f"키움 API 오류: {response_data.get('return_msg', '알 수 없는 오류')}")

            # 🚨 반환: 상위 종목 리스트만 추출하여 반환
            return response_data.get("trde_prica_upper", [])

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"네트워크 오류로 거래대금 상위 조회에 실패했습니다: {e}")