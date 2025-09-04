
import pandas as pd
import numpy as np
from src.indicator_calculator import add_bollinger_bands

def test_add_bollinger_bands():
    # 1. 테스트 데이터 생성
    data = {
        'Close': [
            100, 102, 104, 103, 105, 106, 108, 110, 109, 107,
            108, 110, 112, 111, 113, 114, 116, 118, 117, 115
        ]
    }
    df = pd.DataFrame(data)

    # 2. 함수 실행
    window = 5
    df_bb = add_bollinger_bands(df.copy(), window=window, std=2)

    # 3. 결과 검증
    # 마지막 값에 대해 계산
    last_window_data = df['Close'].iloc[-window:]
    expected_middle = np.mean(last_window_data)
    expected_std = np.std(last_window_data, ddof=0) # pandas default ddof=0 for .std()
    
    # pandas rolling.std() default ddof=1, so we recalculate for assertion
    expected_std_pandas = np.std(last_window_data, ddof=1)
    expected_upper = expected_middle + (expected_std_pandas * 2)
    expected_lower = expected_middle - (expected_std_pandas * 2)

    latest_row = df_bb.iloc[-1]

    assert latest_row['BB_Middle'] == expected_middle
    assert np.isclose(latest_row['BB_Upper'], expected_upper)
    assert np.isclose(latest_row['BB_Lower'], expected_lower)
    assert 'BB_Upper' in df_bb.columns
    assert 'BB_Lower' in df_bb.columns

    # Check for NaNs in the beginning
    assert pd.isna(df_bb['BB_Middle'].iloc[window-2])
    assert not pd.isna(df_bb['BB_Middle'].iloc[window-1])
