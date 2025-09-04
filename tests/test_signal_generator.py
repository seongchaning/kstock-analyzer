
import pandas as pd
from src.signal_generator import generate_signals

def test_generate_signals():
    # 1. 시나리오별 테스트 데이터 생성
    
    # 매수(BUY) 시나리오: 종가가 하단 밴드보다 낮음
    df_buy = pd.DataFrame({
        'Close': [100, 95],
        'BB_Upper': [110, 108],
        'BB_Lower': [98, 96]
    })
    
    # 매도(SELL) 시나리오: 종가가 상단 밴드보다 높음
    df_sell = pd.DataFrame({
        'Close': [100, 115],
        'BB_Upper': [110, 112],
        'BB_Lower': [90, 92]
    })
    
    # 관망(HOLD) 시나리오: 종가가 밴드 내에 있음
    df_hold = pd.DataFrame({
        'Close': [100, 105],
        'BB_Upper': [110, 110],
        'BB_Lower': [90, 90]
    })

    # 데이터 부족 시나리오
    df_nan = pd.DataFrame({
        'Close': [100],
        'BB_Upper': [float('nan')],
        'BB_Lower': [float('nan')]
    })

    # 빈 데이터프레임 시나리오
    df_empty = pd.DataFrame()

    # 2. 결과 검증
    assert generate_signals(df_buy) == 'BUY'
    assert generate_signals(df_sell) == 'SELL'
    assert generate_signals(df_hold) == 'HOLD'
    assert generate_signals(df_nan) == 'HOLD'
    assert generate_signals(df_empty) == 'HOLD'
