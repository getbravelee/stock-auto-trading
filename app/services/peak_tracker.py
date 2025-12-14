class PeakTracker:
    """
    주어진 분봉 데이터를 기반으로 '기준 고점'을 추적하고,
    '8% 이상 하락 후 4% 이상 반등' 조건을 감시하여 고점을 초기화하는 클래스입니다.
    """

    def __init__(self):
        # 현재 추적 중인 기준 고점 (Peak Price)
        # - High Price로 갱신하거나, 반등 시 Close Price로 초기화됨.
        self.current_peak = 0.0

        # 8% 하락 구간에 진입했는지 여부 (True = 4% 반등 대기 상태)
        self.zone_active = False

        # 하락 구간에서 기록된 최저가 (Low Price 기준). 4% 반등의 기준점.
        self.zone_min_price = float('inf')

    def process_bar_data(self, high: float, low: float, close: float):
        """
        분봉 데이터를 처리하여 고점 갱신 및 눌림/반등 조건을 체크합니다.

        :param high: 해당 분봉의 고가 (High Price)
        :param low: 해당 분봉의 저가 (Low Price)
        :param close: 해당 분봉의 종가 (Close Price)
        """

        # 1. 초기 고점 설정
        if self.current_peak == 0.0:
            # 첫 데이터의 고가를 초기 고점으로 설정하고, 다음 턴부터 로직 시작
            self.current_peak = high
            print(f"[초기 설정] 기준 고점: {self.current_peak}")
            return

        if not self.zone_active:
            # =========================================================
            # Case 1: 눌림 구간 비활성화 (새로운 고점 갱신 또는 8% 하락 진입 대기)
            # =========================================================

            # A. 고점 갱신 (High Price 활용)
            # 현재 고점보다 높은 고가(high)가 나오면 고점을 갱신합니다.
            if high > self.current_peak:
                print(f"[고점 갱신] 이전: {self.current_peak} -> 현재: {high}")
                self.current_peak = high
                # 새로운 고점으로부터 하락률을 측정해야 하므로 최저점 추적 가격 초기화
                self.zone_min_price = float('inf')

                # B. 8% 하락 구간 진입 감지 (Low Price 활용)
            # 현재 고점 대비 저가(low)가 8% 이상 하락했는지 확인합니다.
            drop_percentage = (self.current_peak - low) / self.current_peak

            if drop_percentage >= 0.08:
                print(f"[Zone Active] 8% 이상 하락 ({drop_percentage * 100:.2f}%) 감지. 4% 반등 대기 시작.")
                self.zone_active = True

                # 하락 구간의 최저점을 설정합니다.
                self.zone_min_price = min(self.zone_min_price, low)

                # 12% 초과 하락에 대한 정보 (사용자 로직에 따라 이탈 처리는 없으며, 최저점 기준으로 반등 감시)
                if drop_percentage > 0.12:
                    print(f"[경고] 하락률이 12%({drop_percentage * 100:.2f}%)를 초과했지만, 로직에 따라 4% 반등을 계속 감시합니다.")

        else:
            # =========================================================
            # Case 2: 눌림 구간 활성화 (4% 이상 반등 대기)
            # =========================================================

            # B-2. 하락 구간의 최저점 갱신 (Low Price 활용)
            # 4% 반등의 기준이 되는 최저점을 계속 추적합니다.
            if low < self.zone_min_price:
                self.zone_min_price = low
                print(f"[Zone Active] 최저점 갱신: {self.zone_min_price}")

            # C. 4% 반등 조건 충족 확인 (Close Price 활용)
            # 눌림 구간 최저점 대비 종가(close)가 4% 이상 반등했는지 확인합니다.
            rebound_percentage = (close - self.zone_min_price) / self.zone_min_price

            if rebound_percentage >= 0.04:
                print(f"[고점 초기화] 4% 이상 반등 ({rebound_percentage * 100:.2f}%) 충족. 새로운 사이클 시작!")

                # 1. 고점 초기화 및 갱신 (새로운 고점은 반등을 일으킨 종가로 설정)
                self.current_peak = close
                # 2. Zone Active 해제 (다음 High 갱신을 기다림)
                self.zone_active = False
                # 3. Zone Min Price 초기화 (새로운 사이클을 준비)
                self.zone_min_price = float('inf')

    def get_status(self):
        """현재 Tracker의 상태 정보를 반환합니다."""
        status = {
            "기준 고점 (Peak)": self.current_peak,
            "눌림 구간 진입 여부 (Zone Active)": self.zone_active,
            "눌림 구간 최저점 (Zone Min Price)": self.zone_min_price if self.zone_min_price != float('inf') else "N/A"
        }
        return status