
import pandas as pd

def generate_signals(df: pd.DataFrame) -> str:
    """
    볼린저 밴드 지표가 포함된 데이터프레임을 기반으로 매매 신호를 생성합니다.

    - 매수 신호: 종가가 하단 밴드 아래로 내려갔을 때
    - 매도 신호: 종가가 상단 밴드 위로 올라갔을 때
    - 관망 신호: 그 외

    :param df: 볼린저 밴드 지표가 포함된 데이터프레임
    :return: 'BUY', 'SELL', 또는 'HOLD' 신호 문자열
    """
    if df.empty:
        return 'HOLD'

    latest_data = df.iloc[-1]
    if pd.isna(latest_data['BB_Upper']) or pd.isna(latest_data['BB_Lower']):
        return 'HOLD' # Not enough data to generate a signal

    if latest_data['Close'] < latest_data['BB_Lower']:
        return 'BUY'
    elif latest_data['Close'] > latest_data['BB_Upper']:
        return 'SELL'
    else:
        return 'HOLD'
