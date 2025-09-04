
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import html
import logging

from src.data_provider import get_top_market_cap_stocks, get_price_history, get_stock_name, add_daily_percentage_change
from src.indicator_calculator import add_bollinger_bands, add_rsi, add_macd
from src.signal_generator import generate_signals
from src.gui import render_sidebar, render_main_analysis_summary, render_detailed_chart_analysis, create_main_chart, create_volume_chart, create_rsi_chart, create_macd_chart

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(layout="wide")




# --- 사이드바 --- #
params = render_sidebar()
date_to_check = params["date_to_check"]
date_str = params["date_str"]
stock_limit = params["stock_limit"]
show_bb = params["show_bb"]
bb_window = params["bb_window"]
bb_std = params["bb_std"]
show_rsi = params["show_rsi"]
rsi_window = params["rsi_window"]
show_macd = params["show_macd"]
macd_short = params["macd_short"]
macd_long = params["macd_long"]
macd_signal = params["macd_signal"]


# --- 메인 화면 --- #
st.title("KOSPI 상위 종목 매매 신호 분석")
st.write(f"{date_to_check.strftime('%Y년 %m월 %d일')} 기준 시가총액 상위 {stock_limit}개 종목")

if 'results' not in st.session_state or st.sidebar.button("분석 시작", use_container_width=True):
    try:
        with st.spinner("KOSPI 시가총액 상위 종목을 가져오는 중..."):
            top_stocks = get_top_market_cap_stocks(date_str, limit=stock_limit)
        st.success(f"상위 {len(top_stocks)}개 종목을 성공적으로 가져왔습니다.")

        start_date = (date_to_check - timedelta(days=max(bb_window, rsi_window, macd_long) * 2)).strftime("%Y%m%d")
        end_date = date_str

        results = []
        progress_bar = st.progress(0, text="종목별 분석 진행 중...")

        for i, ticker in enumerate(top_stocks):
            stock_name = html.escape(get_stock_name(ticker))
            progress_text = f"({i+1}/{len(top_stocks)}) {stock_name} ({ticker}) 분석 중..."
            progress_bar.progress((i + 1) / len(top_stocks), text=progress_text)

            df = get_price_history(ticker, start_date, end_date)
            if df.empty: continue

            df = add_bollinger_bands(df.copy(), window=bb_window, std=bb_std)
            df = add_rsi(df.copy(), window=rsi_window)
            df = add_macd(df.copy(), short_window=macd_short, long_window=macd_long, signal_window=macd_signal)
            
            # Generate signals for each row for plotting
            df['signal'] = df.apply(lambda row: generate_signals(pd.DataFrame([row])), axis=1)

            results.append({
                "ticker": ticker, "name": stock_name,
                "signal": df.iloc[-1]['signal'], "close": df.iloc[-1]['Close'],
                "df": df
            })
        progress_bar.empty()
        st.session_state['results'] = results

    except Exception as e:
        logging.error(f"분석 중 예기치 않은 오류 발생: {e}", exc_info=True)
        st.error("오류가 발생하여 분석을 완료할 수 없습니다. 서버 로그를 확인해주세요.")

if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']
    
    render_main_analysis_summary(results)

    indicators_to_show = []
    if show_bb: indicators_to_show.append('bb')
    if show_rsi: indicators_to_show.append('rsi')
    if show_macd: indicators_to_show.append('macd')

    # Pass the selected stock name from the previous session if available
    selected_stock_name_from_session = st.session_state.get('selected_stock_name', None)
    render_detailed_chart_analysis(results, selected_stock_name_from_session, indicators_to_show)
    # Update session state with the currently selected stock name for persistence
    st.session_state['selected_stock_name'] = st.session_state['selected_stock_name'] # This line is redundant, but ensures the key exists

