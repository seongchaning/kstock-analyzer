
import pandas as pd

def add_bollinger_bands(df: pd.DataFrame, window: int = 20, std: int = 2) -> pd.DataFrame:
    """
    데이터프레임에 볼린저 밴드 지표를 추가합니다.
    """
    df['BB_Middle'] = df['Close'].rolling(window=window).mean()
    df['BB_Std'] = df['Close'].rolling(window=window).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * std)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * std)
    return df

def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    데이터프레임에 RSI 지표를 추가합니다.
    """
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def add_macd(df: pd.DataFrame, short_window: int = 12, long_window: int = 26, signal_window: int = 9) -> pd.DataFrame:
    """
    데이터프레임에 MACD 지표를 추가합니다.
    """
    df['MACD_Short_EMA'] = df['Close'].ewm(span=short_window, adjust=False).mean()
    df['MACD_Long_EMA'] = df['Close'].ewm(span=long_window, adjust=False).mean()
    df['MACD'] = df['MACD_Short_EMA'] - df['MACD_Long_EMA']
    df['MACD_Signal'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()
    return df
