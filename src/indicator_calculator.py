
import pandas as pd

def add_bollinger_bands(df: pd.DataFrame, window: int = 20, std: int = 2) -> pd.DataFrame:
    """
    데이터프레임에 볼린저 밴드 지표를 추가합니다.

    :param df: 시세 데이터프레임 (반드시 'Close' 컬럼 포함)
    :param window: 이동 평균 기간
    :param std: 표준 편차
    :return: 볼린저 밴드가 추가된 데이터프레임
    """
    df['BB_Middle'] = df['Close'].rolling(window=window).mean()
    df['BB_Std'] = df['Close'].rolling(window=window).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * std)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * std)
    return df
