from pydantic import BaseModel, Field
from typing import List

class MinPoleChartData(BaseModel):
    # API 응답에서 "-"가 붙어있는 현재가(cur_prc) 등을 Float 타입으로 변환
    cur_prc: float = Field(alias="cur_prc")
    high_pric: float = Field(alias="high_pric")
    low_pric: float = Field(alias="low_pric")
    cntr_tm: str = Field(alias="cntr_tm") # 체결 시간 (문자열 유지)

    # API 응답 문자열을 Float으로 변환하는 로직 (Pydantic의 Field Validator를 활용할 수 있으나, 여기서는 간단히 모델만 정의)
    # 실제 구현에서는 API 응토의 "-" 기호를 제거하고 float으로 변환해야 합니다.
    @classmethod
    def from_api_response(cls, data: dict):
        # "-"를 제거하고 숫자로 변환
        processed_data = {
            "cur_prc": float(data.get("cur_prc", "0").replace("-", "")),
            "high_pric": float(data.get("high_pric", "0").replace("-", "")),
            "low_pric": float(data.get("low_pric", "0").replace("-", "")),
            "cntr_tm": data.get("cntr_tm")
        }
        return cls(**processed_data)

class ChartAnalysisResult(BaseModel):
    symbol: str
    peak_tracker_status: List[dict]
    final_peak: float