
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import html
import logging

from src.data_provider import get_top_market_cap_stocks, get_price_history, get_stock_name
from src.indicator_calculator import add_bollinger_bands
from src.signal_generator import generate_signals

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(layout="wide")

# --- 사이드바 --- #
st.sidebar.title("📈 KOSPI 분석 설정")

today = datetime.today()

# st.date_input은 datetime.date 객체를 반환하므로, 문자열로 변환 필요
date_to_check = st.sidebar.date_input("기준일", today, max_value=today)
date_str = date_to_check.strftime("%Y%m%d")

stock_limit = st.sidebar.slider("분석할 종목 수", 10, 50, 20)

st.sidebar.header("기술적 지표 설정")
bb_window = st.sidebar.slider("볼린저 밴드 기간 (일)", 5, 60, 20)
bb_std = st.sidebar.slider("볼린저 밴드 표준편차", 1.0, 3.0, 2.0, 0.1)

# --- 메인 화면 --- #
st.title("KOSPI 상위 종목 매매 신호 분석")
st.write(f"{date_to_check.strftime('%Y년 %m월 %d일')} 기준 시가총액 상위 {stock_limit}개 종목")

if st.sidebar.button("분석 시작", use_container_width=True):
    try:
        with st.spinner("KOSPI 시가총액 상위 종목을 가져오는 중..."):
            top_stocks = get_top_market_cap_stocks(date_str, limit=stock_limit)

        st.success(f"상위 {len(top_stocks)}개 종목을 성공적으로 가져왔습니다.")

        # 분석 기간 설정 (볼린저 밴드 기간 + 추가 여유분)
        start_date = (date_to_check - timedelta(days=bb_window * 2)).strftime("%Y%m%d")
        end_date = date_str

        # 결과를 저장할 리스트
        results = []

        progress_bar = st.progress(0, text="종목별 분석 진행 중...")

        for i, ticker in enumerate(top_stocks):
            # [보안 강화] XSS 방지를 위해 외부에서 온 종목명을 이스케이프 처리
            stock_name = html.escape(get_stock_name(ticker))
            
            progress_text = f"({i+1}/{len(top_stocks)}) {stock_name} ({ticker}) 분석 중..."
            progress_bar.progress((i + 1) / len(top_stocks), text=progress_text)

            # 데이터 가져오기 및 분석
            df = get_price_history(ticker, start_date, end_date)
            if df.empty:
                continue
            
            df_bb = add_bollinger_bands(df.copy(), window=bb_window, std=bb_std)
            signal = generate_signals(df_bb)

            results.append({
                "ticker": ticker,
                "name": stock_name,
                "signal": signal,
                "close": df_bb.iloc[-1]['Close'],
                "df": df_bb
            })

        progress_bar.empty()

        st.subheader("📊 분석 결과 요약")

        # 신호에 따른 이모티콘/색상
        def get_signal_display(signal):
            if signal == 'BUY':
                return f"🟢 매수"
            elif signal == 'SELL':
                return f"🔴 매도"
            else:
                return f"⚪ 관망"

        # 요약 테이블 생성
        summary_df = pd.DataFrame([{
            "종목명": res["name"],
            "티커": res["ticker"],
            "현재가": f"{res['close']:,.0f}원",
            "신호": get_signal_display(res["signal"])
        } for res in results])

        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.subheader("📈 상세 차트 보기")
        for res in results:
            expander_title = f"{res['name']} ({res['ticker']}) - {get_signal_display(res['signal'])}"
            with st.expander(expander_title):
                fig = go.Figure()

                # 주가 캔들스틱 차트
                fig.add_trace(go.Candlestick(x=res['df'].index, 
                                           open=res['df']['Open'], 
                                           high=res['df']['High'], 
                                           low=res['df']['Low'], 
                                           close=res['df']['Close'], 
                                           name='주가'))

                # 볼린저 밴드
                fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['BB_Upper'], mode='lines', name='상단 밴드', line=dict(color='red', dash='dash')))
                fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['BB_Middle'], mode='lines', name='중심선', line=dict(color='orange', dash='dot')))
                fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['BB_Lower'], mode='lines', name='하단 밴드', line=dict(color='blue', dash='dash')))

                fig.update_layout(
                    title=f"{res['name']} 볼린저 밴드 차트",
                    xaxis_title="날짜",
                    yaxis_title="가격(원)",
                    legend_title="지표",
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        # [보안 강화] 상세 오류는 로그로 기록하고, 사용자에게는 일반적인 메시지를 표시
        logging.error(f"분석 중 예기치 않은 오류 발생: {e}", exc_info=True)
        st.error("오류가 발생하여 분석을 완료할 수 없습니다. 서버 로그를 확인해주세요.")

